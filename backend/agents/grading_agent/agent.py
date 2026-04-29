"""
backend/agents/grading_agent/agent.py
---------------------------------------
ONE unified LangGraph graph for both blueprint creation and per-student grading.

━━━ Why one graph? ━━━
The blueprint is NOT a JSON stored in a database column.
The blueprint IS the LangGraph checkpoint state after the agent has read
the exam paper, optional correction PDF, and relevant lesson pages.
That suspended checkpoint (in Postgres) is the blueprint.

When grading a student, the blueprint checkpoint is FORKED (SQL copy) to a new
thread_id. The student's session resumes from that fork — the agent already has
all the exam knowledge in its context window and only needs to read the one
student's paper on top of that.

━━━ Graph topology ━━━

  START
    ↓
  bp_agent_node  ←─────────────────────────────────────────────────┐
    ↓ tool_calls                                                    │
  bp_tools_node ───────────────────────────────────────────────────┘
    ↓ no tool_calls
  bp_interrupt_node   ← interrupt() HERE = THE BLUEPRINT CHECKPOINT
    │                   suspended waiting for {"student_exam_path": "..."}
    ↓ resume
  grade_agent_node  ←──────────────────────────────────────────────┐
    ↓ tool_calls                                                    │
  grade_tools_node ────────────────────────────────────────────────┘
    ↓ no tool_calls
  grade_interrupt_node  ← interrupt() HERE = teacher HIL
    │                     suspended waiting for teacher decisions
    ↓ resume
  END

━━━ Phase 1 (blueprint creation) ━━━
  Route runs the graph from START on a fresh thread.
  Agent reads exam PDF + correction PDF + lesson docs via RAG.
  Graph suspends at bp_interrupt_node (that suspended state IS the blueprint).
  Route stores analysis_thread_id in GradingBlueprint.

━━━ Phase 2 (student grading) ━━━
  Route forks blueprint checkpoint → student thread (db.fork_thread()).
  Route resumes student thread with Command(resume={"student_exam_path": "..."}).
  Agent reads only the student's exam (exam context already in the forked state).
  Agent grades per-question, emitting question_result custom events.
  Graph suspends at grade_interrupt_node for teacher HIL.
  Teacher approves/edits → route calls Command(resume=decisions) → grades saved.

LLM: ChatOpenAIWithReasoning (same as pedagogical agent).
"""
import json
import logging
from typing import Annotated, Any, List, Literal, Optional

from langchain_core.messages import (
    AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from typing_extensions import TypedDict

from backend.config import HF_ENDPOINT_URL, HF_TOKEN, VLM_MODEL
from backend.agents.reasoningchatopenai import ChatOpenAIWithReasoning
from backend.agents.grading_agent.tools import read_pdf_as_images, rag_retrieve

logger = logging.getLogger(__name__)


# ─── LLM factory ──────────────────────────────────────────────────────────────

def _make_llm(reasoning: bool) -> ChatOpenAIWithReasoning:
    return ChatOpenAIWithReasoning(
        model=VLM_MODEL,
        api_key=HF_TOKEN,
        base_url=HF_ENDPOINT_URL,
        streaming=True,
        max_tokens=8192,
        temperature=0.6 if reasoning else 0.7,
        top_p=0.95 if reasoning else 0.8,
        extra_body={
            "top_k": 20,
            "min_p": 0.0,
            "presence_penalty": 0.0,
            "think": reasoning,
            "chat_template_kwargs": {
                "enable_thinking": reasoning,
                "preserve_thinking": True,
            },
        },
    )


# ─── Reasoning extractor ──────────────────────────────────────────────────────

from backend.agents.reasoningchatopenai import _extract_reasoning


# ─── Tool result → multimodal content ─────────────────────────────────────────

def _pdf_pages_to_content(tool_msg: ToolMessage) -> list | str:
    """Convert read_pdf_as_images output to multimodal content blocks."""
    try:
        pages = (
            json.loads(tool_msg.content)
            if isinstance(tool_msg.content, str)
            else tool_msg.content
        )
    except (json.JSONDecodeError, TypeError):
        return tool_msg.content
    if not isinstance(pages, list) or not pages:
        return "No pages returned."
    blocks = []
    for page in pages:
        num = page.get("page_number", "?")
        label = f"[Page {num + 1}]" if isinstance(num, int) else f"[Page {num}]"
        blocks.append({"type": "text", "text": label})
        b64 = page.get("image_b64", "")
        if b64:
            blocks.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    return blocks


def _rag_pages_to_content(tool_msg: ToolMessage) -> list | str:
    """Convert rag_retrieve output to multimodal content blocks."""
    try:
        pages = (
            json.loads(tool_msg.content)
            if isinstance(tool_msg.content, str)
            else tool_msg.content
        )
    except (json.JSONDecodeError, TypeError):
        return tool_msg.content
    if not isinstance(pages, list) or not pages:
        return "No relevant pages found."
    blocks = []
    for page in pages:
        blocks.append({"type": "text", "text": f"[Doc {page['doc_id']}, Page {page['page_number'] + 1}]"})
        blocks.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{page['image_b64']}"}})
    return blocks


# ─── State ────────────────────────────────────────────────────────────────────

class GradingGraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

    # ── Blueprint phase inputs (set at graph start) ──
    lesson_doc_ids: List[str]
    exam_file_path: str
    correction_file_path: Optional[str]
    preferences: str
    style_guide: str
    reasoning: bool

    # ── Grading phase inputs (populated when resuming from blueprint interrupt) ──
    student_exam_path: str

    # ── Outputs ──
    breakdown: List[dict]      # per-question results emitted by grade_agent
    teacher_decisions: dict    # teacher review payload from grade_interrupt


# ─── System prompts ───────────────────────────────────────────────────────────

_BP_SYSTEM = """You are an exam correction specialist. Your job is to fully understand this exam paper
so that you can grade multiple students' answers accurately and consistently.

━━━ WHAT TO DO ━━━
1. Call read_pdf_as_images(exam_file_path, max_px) to read the exam paper.
   Choose max_px: 512 plain text | 768 dense/formulas | 1280 diagrams | 1536 technical.
2. If correction_file_path is provided, call read_pdf_as_images(correction_file_path, max_px).
3. If you need lesson context to clarify a question, call rag_retrieve(query, doc_ids, max_px).
4. Apply the teacher's preferences and style guide.

━━━ WHEN DONE ━━━
Write a concise blueprint summary listing each question, its max points, and key criteria.
This summary will be shown to the teacher. Format it clearly — one question per line."""

_GRADE_SYSTEM = """You are grading a student's exam. You have already fully analysed the exam paper
and correction in your previous context. Now read only this student's answers.

━━━ STEPS ━━━
1. Call read_pdf_as_images(student_exam_path, max_px) to see the student's answers.
   Choose max_px based on content: 512 plain text | 768 formulas/tables | 1280 diagrams.
2. Grade EVERY question from the exam. Do not skip any.
3. Compare each answer strictly against what you already know from the exam/correction.

━━━ OUTPUT FORMAT ━━━
For each question, output ONE JSON object on its own line (no extra text around it):
{"question_number": 1, "label": "Q1", "max_points": 4.0, "awarded_points": 3.0, "reasoning": "Identified X correctly but missed Y (-1pt)."}

After ALL questions output this exact line and nothing after it:
GRADING_COMPLETE"""


# ─── Helper: build LLM message list from state ────────────────────────────────

def _build_lc_messages(state: GradingGraphState, system: str) -> list:
    lc: list = [SystemMessage(content=system)]
    for msg in state["messages"]:
        if isinstance(msg, SystemMessage):
            continue
        if msg.type == "human":
            lc.append(HumanMessage(content=msg.content))
        elif msg.type == "ai":
            lc.append(AIMessage(content=msg.content or "", tool_calls=getattr(msg, "tool_calls", [])))
        elif msg.type == "tool":
            name = getattr(msg, "name", "")
            if name == "read_pdf_as_images":
                rich = _pdf_pages_to_content(msg)  # type: ignore[arg-type]
            elif name == "rag_retrieve":
                rich = _rag_pages_to_content(msg)  # type: ignore[arg-type]
            else:
                rich = msg.content
            lc.append(HumanMessage(content=rich))
    return lc


# ─── Parse grading output ─────────────────────────────────────────────────────

def _parse_grading_output(content: str) -> List[dict]:
    results = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line == "GRADING_COMPLETE":
            continue
        try:
            obj = json.loads(line)
            if "question_number" in obj and "awarded_points" in obj:
                results.append(obj)
        except json.JSONDecodeError:
            pass
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  BLUEPRINT PHASE NODES
# ══════════════════════════════════════════════════════════════════════════════

_BP_TOOLS: List[BaseTool] = [read_pdf_as_images, rag_retrieve]
_BP_TOOL_NODE = ToolNode(_BP_TOOLS)


async def bp_tools_node(state: GradingGraphState) -> dict:
    writer = get_stream_writer()
    result = await _BP_TOOL_NODE.ainvoke(state)
    for msg in result.get("messages", []):
        name = getattr(msg, "name", None)
        if name in ("read_pdf_as_images", "rag_retrieve"):
            writer({"type": "tool_result", "name": name,
                    "content": f"Loaded {name} ({len(str(msg.content))} chars)",
                    "tool_call_id": getattr(msg, "tool_call_id", "")})
    return result


async def bp_agent_node(state: GradingGraphState) -> dict:
    writer = get_stream_writer()
    reasoning: bool = state.get("reasoning", False)
    doc_ids = state.get("lesson_doc_ids", [])

    system = _BP_SYSTEM
    system += f"\n\nexam_file_path = {state['exam_file_path']}"
    if state.get("correction_file_path"):
        system += f"\ncorrection_file_path = {state['correction_file_path']}"
    if doc_ids:
        system += f"\nLesson doc_ids for rag_retrieve: {json.dumps(doc_ids)}"
    if state.get("preferences"):
        system += f"\n\nTeacher preferences:\n{state['preferences']}"
    if state.get("style_guide"):
        system += f"\n\nStyle guide:\n{state['style_guide']}"

    lc_messages = _build_lc_messages(state, system)
    if not reasoning:
        lc_messages.append(AIMessage(content="<think>\n</think>"))

    llm = _make_llm(reasoning).bind_tools(_BP_TOOLS)
    response: AIMessage = await llm.ainvoke(lc_messages)

    final_reasoning = _extract_reasoning(response)
    if final_reasoning:
        response.additional_kwargs["reasoning"] = final_reasoning

    for tc in getattr(response, "tool_calls", []) or []:
        writer({"type": "tool_call", "name": tc.get("name", ""),
                "args": tc.get("args", {}), "id": tc.get("id", "")})

    return {"messages": [response]}


async def bp_interrupt_node(state: GradingGraphState) -> dict:
    """
    The blueprint checkpoint IS this suspended state.
    Emit blueprint_ready, then interrupt() waiting for student exam path.
    Resume payload: {"student_exam_path": "/absolute/path/to/student.pdf"}
    """
    writer = get_stream_writer()
    writer({"type": "blueprint_ready"})
    resume = interrupt({"phase": "blueprint_complete"})
    return {"student_exam_path": resume.get("student_exam_path", "")}


def bp_should_continue(state: GradingGraphState) -> Literal["bp_tools", "bp_interrupt_node"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "bp_tools"
    return "bp_interrupt_node"


# ══════════════════════════════════════════════════════════════════════════════
#  GRADING PHASE NODES
# ══════════════════════════════════════════════════════════════════════════════

_GRADE_TOOLS: List[BaseTool] = [read_pdf_as_images]
_GRADE_TOOL_NODE = ToolNode(_GRADE_TOOLS)


async def grade_tools_node(state: GradingGraphState) -> dict:
    writer = get_stream_writer()
    result = await _GRADE_TOOL_NODE.ainvoke(state)
    for msg in result.get("messages", []):
        if getattr(msg, "name", None) == "read_pdf_as_images":
            writer({"type": "tool_result", "name": "read_pdf_as_images",
                    "content": f"Loaded student exam ({len(str(msg.content))} chars)",
                    "tool_call_id": getattr(msg, "tool_call_id", "")})
    return result


async def grade_agent_node(state: GradingGraphState) -> dict:
    writer = get_stream_writer()
    reasoning: bool = state.get("reasoning", False)

    system = _GRADE_SYSTEM
    system += f"\n\nstudent_exam_path = {state.get('student_exam_path', '')}"

    lc_messages = _build_lc_messages(state, system)
    if not reasoning:
        lc_messages.append(AIMessage(content="<think>\n</think>"))

    llm = _make_llm(reasoning).bind_tools(_GRADE_TOOLS)
    response: AIMessage = await llm.ainvoke(lc_messages)

    final_reasoning = _extract_reasoning(response)
    if final_reasoning:
        response.additional_kwargs["reasoning"] = final_reasoning

    for tc in getattr(response, "tool_calls", []) or []:
        writer({"type": "tool_call", "name": tc.get("name", ""),
                "args": tc.get("args", {}), "id": tc.get("id", "")})

    # Parse breakdown when grading is complete
    breakdown: List[dict] = state.get("breakdown", [])
    content_str = response.content if isinstance(response.content, str) else ""
    if "GRADING_COMPLETE" in content_str and not getattr(response, "tool_calls", None):
        breakdown = _parse_grading_output(content_str)
        for q in breakdown:
            writer({
                "type": "question_result",
                "question_number": q.get("question_number"),
                "label": q.get("label", f"Q{q.get('question_number')}"),
                "max_points": q.get("max_points", 0),
                "awarded_points": q.get("awarded_points", 0),
                "reasoning": q.get("reasoning", ""),
            })
        logger.info("grade_agent_node: %d questions graded", len(breakdown))

    return {"messages": [response], "breakdown": breakdown}


async def grade_interrupt_node(state: GradingGraphState) -> dict:
    """
    Emit interrupt event with full breakdown, then suspend for teacher HIL review.
    Resume payload: {"decisions": [{question_number, awarded_points}], "action": "approve"|"cancel"}
    """
    breakdown = state.get("breakdown", [])
    writer = get_stream_writer()
    writer({"type": "interrupt", "breakdown": breakdown})
    decisions = interrupt(breakdown)
    return {"teacher_decisions": decisions}


def grade_should_continue(state: GradingGraphState) -> Literal["grade_tools", "grade_interrupt_node"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "grade_tools"
    return "grade_interrupt_node"


# ══════════════════════════════════════════════════════════════════════════════
#  GRAPH ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════

def _build_graph(checkpointer: AsyncPostgresSaver) -> Any:
    g = StateGraph(GradingGraphState)

    # Blueprint phase
    g.add_node("bp_agent", bp_agent_node)
    g.add_node("bp_tools", bp_tools_node)
    g.add_node("bp_interrupt_node", bp_interrupt_node)

    # Grading phase
    g.add_node("grade_agent", grade_agent_node)
    g.add_node("grade_tools", grade_tools_node)
    g.add_node("grade_interrupt_node", grade_interrupt_node)

    # Blueprint phase edges
    g.add_edge(START, "bp_agent")
    g.add_conditional_edges("bp_agent", bp_should_continue)
    g.add_edge("bp_tools", "bp_agent")

    # Transition: after bp_interrupt resumes, go to grade_agent
    g.add_edge("bp_interrupt_node", "grade_agent")

    # Grading phase edges
    g.add_conditional_edges("grade_agent", grade_should_continue)
    g.add_edge("grade_tools", "grade_agent")
    g.add_edge("grade_interrupt_node", END)

    return g.compile(checkpointer=checkpointer)


_graph: Any = None


async def get_grading_graph() -> Any:
    """Lazily initialise the unified grading graph using the shared pool."""
    global _graph
    if _graph is None:
        from backend.agents.db import get_checkpointer
        checkpointer = await get_checkpointer()
        _graph = _build_graph(checkpointer)
    return _graph

