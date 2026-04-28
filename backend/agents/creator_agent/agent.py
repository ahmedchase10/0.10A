"""
backend/agents/creator_agent/agent.py
---------------------------------------
LangGraph graph for the Creator Agent — AI exam generator.

Graph topology:
  START
    ↓
  creator_node  ←────────────────── (loops while tool_calls)
    ↓ tool_calls                                ↑
  creator_tools_node ─────────────────────────┘
    ↓ no tool_calls (exam draft produced)
  evaluator_node  ←──────────────── (loops while tool_calls)
    ↓ tool_calls                                ↑
  evaluator_tools_node ───────────────────────┘
    ↓ no tool_calls
  route_after_eval
    ├── loop_count < 2 AND flagged questions → creator_node
    └── otherwise → END

Streaming: graph.astream(stream_mode=["messages","custom"])
  - "messages" → per-token AIMessageChunk (content + thinking)
  - "custom"   → tool_call/tool_result/exam_draft/evaluator_feedback events via get_stream_writer()

Checkpointer: AsyncPostgresSaver (shared pool from backend.agents.db)
LLM: Qwen3.6 via HuggingFace endpoint (OpenAI-compatible), ChatOpenAIWithReasoning
"""
import json
import logging
import re
import sys
from typing import Annotated, Any, List, Literal, Optional

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langchain_core.messages import (
    AIMessage, AIMessageChunk, AnyMessage, HumanMessage, SystemMessage, ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from backend.config import HF_ENDPOINT_URL, HF_TOKEN, VLM_MODEL
from backend.agents.reasoningchatopenai import ChatOpenAIWithReasoning
from backend.agents.creator_agent.tools import get_doc_overviews, rag_retrieve

logger = logging.getLogger(__name__)

# ─── Tools registries ─────────────────────────────────────────────────────────

CREATOR_TOOLS: List[BaseTool] = [get_doc_overviews, rag_retrieve]
EVALUATOR_TOOLS: List[BaseTool] = [rag_retrieve]

_CREATOR_TOOL_NODE = ToolNode(CREATOR_TOOLS)
_EVALUATOR_TOOL_NODE = ToolNode(EVALUATOR_TOOLS)

# ─── Agent state ──────────────────────────────────────────────────────────────

class CreatorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    doc_ids: List[str]
    preferences: dict
    reasoning: bool
    loop_count: int             # how many evaluator loops have run (max 2)
    exam_draft: Optional[dict]  # last generated exam JSON (parsed)
    evaluator_feedback: Optional[str]  # feedback from evaluator, injected into next creator turn


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
            "think": reasoning,
            "chat_template_kwargs": {
                "enable_thinking": reasoning,
                "preserve_thinking": True,
            },
        },
    )


# ─── Reasoning extraction ─────────────────────────────────────────────────────

from backend.agents.reasoningchatopenai import _extract_reasoning

# ─── Exam JSON extraction helper ──────────────────────────────────────────────

def _extract_json_object(text: str) -> Optional[dict]:
    """
    Robustly extract the first valid JSON object from text.
    Strategy:
      1. Look for a ```json ... ``` fenced block and parse it with raw_decode
         (handles nesting correctly — doesn't stop at first inner `}`)
      2. Fall back to scanning the full text for the first `{` and using raw_decode
    """
    decoder = json.JSONDecoder()

    # 1. Try fenced block first — find ```json or ``` then decode from the first `{`
    for fence_match in re.finditer(r"```(?:json)?\s*", text):
        start = fence_match.end()
        brace = text.find("{", start)
        if brace == -1:
            continue
        try:
            obj, _ = decoder.raw_decode(text, brace)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    # 2. Scan entire text for first `{` and try raw_decode from there
    brace = text.find("{")
    while brace != -1:
        try:
            obj, _ = decoder.raw_decode(text, brace)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        brace = text.find("{", brace + 1)

    return None


def _extract_exam_json(text: str) -> Optional[dict]:
    obj = _extract_json_object(text)
    if obj and "questions" in obj and isinstance(obj["questions"], list):
        return obj
    return None


def _extract_evaluator_result(text: str) -> Optional[dict]:
    obj = _extract_json_object(text)
    if obj and "flagged" in obj:
        return obj
    return None


# ─── System prompts ───────────────────────────────────────────────────────────

_CREATOR_SYSTEM = """\
You are an expert exam creator assistant helping a teacher design a high-quality exam.

━━━ WORKFLOW ━━━

Step 1 — Understand the material
  Call get_doc_overviews(doc_ids) FIRST.
  Read the sections, subsections, and topics carefully.
  Identify which topics align with the teacher's requested topics (in preferences).

Step 2 — Retrieve relevant pages
  For each question you plan to write, call rag_retrieve(query, doc_ids, max_px) to fetch the
  relevant pages. Ground EVERY question in retrieved material — do NOT fabricate questions
  about content you have not actually retrieved.
  Choose max_px based on content type (512 text / 768 tables-formulas / 900 detailed).

Step 3 — Generate the exam
  Respect the teacher's preferences exactly:
    - difficulty_distribution: percentage of questions per difficulty (easy/medium/hard)
    - exercise_types: only use the requested types (mcq, open, table, fill, true-false)
    - question_count: generate exactly this many questions
    - total_points: distribute points so they sum to exactly this value
    - topics: focus on these topics; if a topic is not in the documents, note it clearly
    - language: write all questions in this language
    - notes: follow any additional instructions exactly

  For MCQ questions include 4 options (A/B/C/D) and mark the correct one in suggested_answer.
  For table questions specify the table structure (rows/columns and what to fill).

Step 4 — Output the exam
  Output the final exam as a JSON block wrapped in ```json ... ```.
  The JSON must have this exact shape:
  {
    "questions": [
      {
        "id": "q1",
        "text": "...",
        "type": "mcq|open|table|fill|true-false",
        "difficulty": "easy|medium|hard",
        "max_points": 2.0,
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],  // MCQ only, omit for other types
        "suggested_answer": "...",
        "source_doc_id": "...",
        "source_hint": "brief description of where in the material"
      }
    ]
  }

━━━ EVALUATOR FEEDBACK ━━━
If evaluator feedback is present in this prompt, you MUST fix the flagged questions specifically.
Do not regenerate the entire exam from scratch — only replace or improve the flagged questions.
Keep all passing questions unchanged.

━━━ QUALITY RULES ━━━
- Every question must be answerable from the retrieved pages
- Do not repeat the same concept across multiple questions
- Difficulty must be proportional to cognitive demand, not just length
- MCQ distractors must be plausible (not obviously wrong)
- Never fabricate answers — only use what the retrieved pages actually contain
"""

_EVALUATOR_SYSTEM = """\
You are a strict exam quality evaluator acting as a student.

Your job: for each question in the exam draft, determine whether it is answerable
from the selected lesson documents alone.

━━━ PROCESS ━━━
For each question:
  1. Call rag_retrieve(suggested_answer_as_query, doc_ids, max_px=768)
  2. Read the retrieved pages
  3. Determine: can a student who read these pages answer this question correctly?

Flag a question if:
  - No retrieved page contains relevant content for that question
  - The suggested_answer is based on information not present in the retrieved pages
  - The question refers to a topic completely absent from the documents

Do NOT flag a question just because it is hard or requires reasoning.

━━━ OUTPUT ━━━
Output your result as a JSON block wrapped in ```json ... ```:
{
  "flagged": [
    {"question_id": "q3", "reason": "No page in the selected docs covers binary trees"},
    {"question_id": "q7", "reason": "Suggested answer references a formula not in any retrieved page"}
  ],
  "pass": false
}

If all questions are well-grounded: output {"flagged": [], "pass": true}
"""


# ─── Tool nodes with custom event emission ────────────────────────────────────

async def creator_tools_node(state: CreatorState) -> dict:
    writer = get_stream_writer()
    result = await _CREATOR_TOOL_NODE.ainvoke(state)
    for msg in result.get("messages", []):
        if getattr(msg, "name", None) == "get_doc_overviews":
            writer({
                "type": "tool_result",
                "name": "get_doc_overviews",
                "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content),
                "tool_call_id": getattr(msg, "tool_call_id", ""),
            })
    return result


async def evaluator_tools_node(state: CreatorState) -> dict:
    result = await _EVALUATOR_TOOL_NODE.ainvoke(state)
    return result


# ─── Creator node ─────────────────────────────────────────────────────────────

async def creator_node(state: CreatorState) -> dict:
    writer = get_stream_writer()
    reasoning: bool = state.get("reasoning", True)
    doc_ids: List[str] = state.get("doc_ids", [])
    preferences: dict = state.get("preferences", {})
    evaluator_feedback: Optional[str] = state.get("evaluator_feedback")
    loop_count: int = state.get("loop_count", 0)

    # Build system prompt
    system_content = _CREATOR_SYSTEM
    system_content += f"\n\n**Active document IDs:** {json.dumps(doc_ids)}"
    system_content += f"\n\n**Teacher preferences:**\n{json.dumps(preferences, indent=2)}"

    if evaluator_feedback:
        system_content += (
            f"\n\n**EVALUATOR FEEDBACK (loop {loop_count}):**\n{evaluator_feedback}\n"
            "You MUST fix the flagged questions. Keep all passing questions unchanged."
        )

    lc_messages: list = [SystemMessage(content=system_content)]

    # On evaluator loop-back, the state contains evaluator messages appended AFTER the
    # creator's exam draft. If we pass those to the creator LLM, it sees orphaned tool_call
    # IDs (evaluator's rag calls followed by HumanMessages instead of ToolMessages), which
    # confuses Qwen. Fix: trim messages to only include up to (and including) the last creator
    # AI message that has content and no tool_calls — that is the exam draft response.
    messages_to_use = list(state["messages"])
    if evaluator_feedback:
        cutoff = len(messages_to_use)
        for i in range(len(messages_to_use) - 1, -1, -1):
            msg = messages_to_use[i]
            if msg.type == "ai" and not getattr(msg, "tool_calls", None) and msg.content:
                cutoff = i + 1
                break
        messages_to_use = messages_to_use[:cutoff]

    for msg in messages_to_use:
        if isinstance(msg, SystemMessage):
            continue
        if msg.type == "human":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.type == "ai":
            lc_messages.append(
                AIMessage(content=msg.content or "", tool_calls=getattr(msg, "tool_calls", []))
            )
        elif msg.type == "tool":
            # Pass tool results back as human messages (handles multimodal rag results)
            from backend.agents.pedagogical_agent.agent import _tool_result_to_image_content
            if getattr(msg, "name", None) == "rag_retrieve":
                rich = _tool_result_to_image_content(msg)
                lc_messages.append(HumanMessage(content=rich))
            else:
                lc_messages.append(HumanMessage(content=msg.content if isinstance(msg.content, str) else json.dumps(msg.content)))

    if not reasoning:
        lc_messages.append(AIMessage(content="<think>\n</think>"))

    llm = _make_llm(reasoning)
    llm_with_tools = llm.bind_tools(CREATOR_TOOLS)
    response: AIMessage = await llm_with_tools.ainvoke(lc_messages)

    # Preserve reasoning
    final_reasoning = _extract_reasoning(response)
    if final_reasoning:
        response.additional_kwargs["reasoning"] = final_reasoning

    # Emit tool_call events
    for tc in getattr(response, "tool_calls", []) or []:
        writer({
            "type": "tool_call",
            "name": tc.get("name", ""),
            "args": tc.get("args", {}),
            "id": tc.get("id", ""),
        })

    # If no tool calls, the creator produced its exam draft
    updates: dict = {"messages": [response]}
    if not getattr(response, "tool_calls", None):
        exam = _extract_exam_json(response.content or "")
        if exam:
            updates["exam_draft"] = exam
            writer({"type": "exam_draft", "questions": exam.get("questions", [])})
        else:
            logger.warning("creator_node: could not parse exam JSON from response")

    return updates


# ─── Evaluator node ───────────────────────────────────────────────────────────

def _find_evaluator_start(messages: list) -> int:
    """
    Find the index in state["messages"] where the evaluator turn begins.
    The evaluator starts AFTER the last creator AI message that has content and no tool_calls
    (that is the exam draft response). Everything after that index belongs to the evaluator.
    Returns len(messages) if no such boundary is found (evaluator hasn't started yet).
    """
    cutoff = len(messages)
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.type == "ai" and not getattr(msg, "tool_calls", None) and msg.content:
            # This is the last creator AI message with content — evaluator starts after it
            cutoff = i + 1
            break
    return cutoff


async def evaluator_node(state: CreatorState) -> dict:
    writer = get_stream_writer()
    doc_ids: List[str] = state.get("doc_ids", [])
    exam_draft: Optional[dict] = state.get("exam_draft")
    loop_count: int = state.get("loop_count", 0)

    if not exam_draft:
        # No draft to evaluate — pass through
        return {"loop_count": loop_count, "evaluator_feedback": None}

    system_content = _EVALUATOR_SYSTEM
    system_content += f"\n\n**Active document IDs:** {json.dumps(doc_ids)}"
    system_content += f"\n\n**Exam draft to evaluate:**\n```json\n{json.dumps(exam_draft, indent=2)}\n```"

    # Build message history for the evaluator.
    # On first entry: start fresh with [SystemMessage, HumanMessage].
    # On re-entry after tool calls: include the evaluator's own tool calls + results from state.
    all_messages = list(state["messages"])
    eval_start = _find_evaluator_start(all_messages)
    eval_messages = all_messages[eval_start:]  # evaluator's own accumulated messages

    lc_messages: list = [SystemMessage(content=system_content)]

    if eval_messages:
        # Re-entry: include evaluator's prior tool calls and results
        for msg in eval_messages:
            if msg.type == "ai":
                lc_messages.append(
                    AIMessage(content=msg.content or "", tool_calls=getattr(msg, "tool_calls", []))
                )
            elif msg.type == "tool":
                # Evaluator's rag_retrieve results → multimodal HumanMessage
                from backend.agents.pedagogical_agent.agent import _tool_result_to_image_content
                rich = _tool_result_to_image_content(msg)
                lc_messages.append(HumanMessage(content=rich))
    else:
        # First entry: prime with the initial human request
        lc_messages.append(HumanMessage(content="Please evaluate each question and output your result."))

    # Evaluator uses reasoning OFF for speed (checking pass, not creative)
    llm = _make_llm(False)
    llm_with_tools = llm.bind_tools(EVALUATOR_TOOLS)
    # Suppress thinking token for evaluator
    lc_messages.append(AIMessage(content="<think>\n</think>"))
    response: AIMessage = await llm_with_tools.ainvoke(lc_messages)

    # Emit tool_call events for evaluator tool usage
    for tc in getattr(response, "tool_calls", []) or []:
        writer({
            "type": "tool_call",
            "name": tc.get("name", ""),
            "args": tc.get("args", {}),
            "id": tc.get("id", ""),
        })

    updates: dict = {"messages": [response]}

    if not getattr(response, "tool_calls", None):
        # Evaluator finished — parse result
        result = _extract_evaluator_result(response.content or "")
        new_loop_count = loop_count + 1

        if result and not result.get("pass", True) and result.get("flagged"):
            feedback = json.dumps(result["flagged"], indent=2)
            writer({
                "type": "evaluator_feedback",
                "flagged": result["flagged"],
                "loop_count": new_loop_count,
            })
            updates["evaluator_feedback"] = feedback
        else:
            updates["evaluator_feedback"] = None

        updates["loop_count"] = new_loop_count

    return updates


# ─── Routing ──────────────────────────────────────────────────────────────────

def should_continue_creator(state: CreatorState) -> Literal["creator_tools", "evaluator"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "creator_tools"
    return "evaluator"


def should_continue_evaluator(state: CreatorState) -> Literal["evaluator_tools", "check_loop"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "evaluator_tools"
    return "check_loop"


def route_after_eval(state: CreatorState) -> Literal["creator", "__end__"]:
    loop_count: int = state.get("loop_count", 0)
    feedback: Optional[str] = state.get("evaluator_feedback")
    if feedback and loop_count < 2:
        return "creator"
    return END


# ─── Graph builder ────────────────────────────────────────────────────────────

def _build_graph(checkpointer: AsyncPostgresSaver) -> Any:
    graph = StateGraph(CreatorState)

    graph.add_node("creator", creator_node)
    graph.add_node("creator_tools", creator_tools_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("evaluator_tools", evaluator_tools_node)

    graph.add_edge(START, "creator")
    graph.add_conditional_edges("creator", should_continue_creator, {
        "creator_tools": "creator_tools",
        "evaluator": "evaluator",
    })
    graph.add_edge("creator_tools", "creator")
    graph.add_conditional_edges("evaluator", should_continue_evaluator, {
        "evaluator_tools": "evaluator_tools",
        "check_loop": "check_loop",
    })
    graph.add_edge("evaluator_tools", "evaluator")

    # check_loop is a pass-through router node
    graph.add_node("check_loop", lambda state: {})
    graph.add_conditional_edges("check_loop", route_after_eval, {
        "creator": "creator",
        END: END,
    })

    return graph.compile(checkpointer=checkpointer)


# ─── Public: lazily initialised compiled graph ────────────────────────────────

_graph = None


async def get_graph() -> Any:
    global _graph
    if _graph is None:
        from backend.agents.db import get_checkpointer
        checkpointer = await get_checkpointer()
        _graph = _build_graph(checkpointer)
    return _graph


async def close_graph() -> None:
    """No-op — pool managed by backend.agents.db.close_pool()."""
    pass

