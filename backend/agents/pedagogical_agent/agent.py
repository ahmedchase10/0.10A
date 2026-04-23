"""
Pedagogical Agent — LangGraph graph definition.

Graph topology:
  agent ──(has tool calls)──► tools ──► agent
        ──(no tool calls)───► END

Streaming: graph.astream(stream_mode=["messages","custom"])
  - "messages" → per-token AIMessageChunk (content + thinking)
  - "custom"   → tool_call/tool_result notifications via get_stream_writer()

Checkpointer: AsyncPostgresSaver with AsyncConnectionPool
  (autocommit=True + row_factory=dict_row — required by langgraph-checkpoint-postgres)

LLM: Qwen3.5 via HuggingFace endpoint (OpenAI-compatible).
     Native tool calling now enabled (--tool-call-parser qwen3_coder on server).
"""
import json
import sys
from typing import Annotated, Any, List, Literal

# ── Windows: psycopg3 async requires SelectorEventLoop ────────────────────────
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage, AIMessage, HumanMessage, AIMessageChunk
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from psycopg.rows import dict_row
from typing_extensions import TypedDict

from backend.config import HF_ENDPOINT_URL, HF_TOKEN, VLM_MODEL, POSTGRES_URL
from backend.agents.pedagogical_agent.tools import rag_retrieve, rewrite_query

# ─── Tools registry ───────────────────────────────────────────────────────────

TOOLS: List[BaseTool] = [rewrite_query, rag_retrieve]
_TOOL_NODE = ToolNode(TOOLS)

# Emit tool_result custom events for tools whose output is human-readable
_TEXT_TOOLS = {"rewrite_query"}

async def tools_node(state: "AgentState") -> dict:
    writer = get_stream_writer()
    result = await _TOOL_NODE.ainvoke(state)
    # result is {"messages": [ToolMessage, ...]}
    for msg in result.get("messages", []):
        if getattr(msg, "name", None) in _TEXT_TOOLS:
            writer({
                "type": "tool_result",
                "name": msg.name,
                "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content),
                "tool_call_id": getattr(msg, "tool_call_id", ""),
            })
    return result

# ─── Postgres URL: strip SQLAlchemy driver prefix for psycopg3 direct use ─────

def _psycopg_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)

# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a rigorous pedagogical assistant helping a teacher prepare and verify course material.
You have two tools: `rewrite_query` and `rag_retrieve`.

━━━ DECISION FLOW ━━━

Step 1 — Do you already have the answer?
  If relevant pages were already retrieved earlier in this conversation and they cover the current question,
  answer directly. Do not re-retrieve or rewrite. Skip to the answer.

Step 2 — Is the query clear enough to search?
  A query is NOT clear if it is so general or ambiguous that even a perfect retrieval would return the wrong pages
  (e.g. "explain this", "what does it mean", "the formula" with no context).
  → If NOT clear: STOP. Ask the user one focused clarifying question. Do not call any tool.

Step 3 — Does the query need rewriting before searching?
  Rewrite ONLY when:
    • The query is multi-step and a single search phrase would serve better
    • The phrasing is very conversational and would produce poor embedding matches
  Do NOT rewrite when the query is already a clean keyword or technical phrase — go directly to `rag_retrieve`.
  Do NOT rewrite when the query is ambiguous — ask the user instead.
  → If rewriting is needed: call `rewrite_query(query)`, then use its output in `rag_retrieve`.
  → Otherwise: call `rag_retrieve` directly.

Step 4 — Retrieve and answer
  Call `rag_retrieve(query, doc_ids, max_px)`.
  Choose max_px by expected visual complexity:
      512  → simple factual / short text
      768  → dense text, formulas, tables
      1280 → diagrams, graphs, schematics
      1536 → highly detailed technical visuals
  If retrieved pages do not contain enough to answer confidently, say so clearly. Never fabricate.

━━━ MATH PROBLEMS ━━━
  Show step-by-step reasoning. Wrap the final answer in \\boxed{}.
  Verify each algebraic step before moving to the next.

━━━ GENERAL ━━━
  Be concise, accurate, and educational. Precision matters over verbosity."""

# ─── Agent state ──────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    doc_ids: List[str]
    reasoning: bool

# ─── Reasoning helpers ────────────────────────────────────────────────────────

def _extract_reasoning_from_ai_message(msg: AIMessage) -> str:
    """Best-effort extraction of assistant reasoning from known LangChain shapes."""
    out = ""

    additional = getattr(msg, "additional_kwargs", None)
    if isinstance(additional, dict):
        for key in ("reasoning", "reasoning_content"):
            val = additional.get(key)
            if isinstance(val, str):
                out += val

    blocks = getattr(msg, "content_blocks", None)
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "reasoning":
                continue
            val = block.get("reasoning") or block.get("text")
            if isinstance(val, str):
                out += val

    return out


# ─── LLM wrapper: keep reasoning deltas from OpenAI-compatible streams ────────

class ChatOpenAIWithReasoning(ChatOpenAI):
    """Preserve provider-native reasoning keys on streamed chunks."""

    def _convert_chunk_to_generation_chunk(self, chunk: dict, default_chunk_class: type, base_generation_info: dict | None):
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if generation_chunk is None:
            return None

        try:
            choices = chunk.get("choices", []) or chunk.get("chunk", {}).get("choices", [])
            if not choices:
                return generation_chunk
            delta = choices[0].get("delta") or {}
            if not isinstance(delta, dict):
                return generation_chunk

            reasoning_tok = delta.get("reasoning") or delta.get("reasoning_content")
            if reasoning_tok and isinstance(generation_chunk.message, AIMessageChunk):
                generation_chunk.message.additional_kwargs["reasoning"] = reasoning_tok
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning_tok
        except Exception:
            # Never break streaming because of metadata extraction.
            pass

        return generation_chunk


# ─── LLM factory ──────────────────────────────────────────────────────────────

def _make_llm(reasoning: bool) -> ChatOpenAIWithReasoning:
    """
    ChatOpenAI pointing at the HuggingFace endpoint.
    - extra_body is the correct place for vLLM-specific params (top_k, chat_template_kwargs)
    - model_kwargs is only for standard OpenAI params not exposed as constructor args
    """
    return ChatOpenAIWithReasoning(
        model=VLM_MODEL,
        api_key=HF_TOKEN,
        base_url=HF_ENDPOINT_URL,
        streaming=True,
        max_tokens=8192,
        temperature=0.6 if reasoning else 0.7,
        top_p=0.95 if reasoning else 0.8,
        # extra_body: vLLM-specific params — do NOT put these in model_kwargs
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

# ─── Convert rag_retrieve tool result to image_url content blocks ─────────────

def _tool_result_to_image_content(tool_msg: ToolMessage) -> list | str:
    """Rewrite rag_retrieve output as multimodal content blocks."""
    try:
        pages: list[dict] = (
            json.loads(tool_msg.content)
            if isinstance(tool_msg.content, str)
            else tool_msg.content
        )
    except (json.JSONDecodeError, TypeError):
        return tool_msg.content

    if not isinstance(pages, list) or not pages:
        return "No relevant pages found in the selected documents."

    blocks = []
    for page in pages:
        blocks.append({"type": "text", "text": f"[Doc {page['doc_id']}, Page {page['page_number'] + 1}]"})
        blocks.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{page['image_b64']}"}})
    return blocks

# ─── Agent node ───────────────────────────────────────────────────────────────

async def agent_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    reasoning: bool = state.get("reasoning", True)
    doc_ids: List[str] = state.get("doc_ids", [])

    # Inject active doc_ids into the system prompt so the LLM always knows them
    system_content = SYSTEM_PROMPT
    if doc_ids:
        system_content += (
            f"\n\n**Active document IDs for this session (always pass to rag_retrieve):** "
            f"{json.dumps(doc_ids)}"
        )

    # Build the message list for the LLM
    lc_messages: list = [SystemMessage(content=system_content)]

    for msg in state["messages"]:
        if isinstance(msg, SystemMessage):
            continue
        if msg.type == "human":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.type == "ai":
            lc_messages.append(
                AIMessage(
                    content=msg.content or "",
                    tool_calls=getattr(msg, "tool_calls", []),
                )
            )
        elif msg.type == "tool":
            # Rewrite rag_retrieve output as multimodal blocks; feed back as HumanMessage
            # so vision content is properly passed to the model
            rich_content = _tool_result_to_image_content(msg)
            lc_messages.append(HumanMessage(content=rich_content))

    # When reasoning is OFF: prefill assistant to suppress <think>
    if not reasoning:
        lc_messages.append(AIMessage(content="<think>\n</think>"))

    llm = _make_llm(reasoning)
    llm_with_tools = llm.bind_tools(TOOLS)

    response: AIMessage = await llm_with_tools.ainvoke(lc_messages)

    # Persist reasoning on the checkpointed assistant message so next turn can resend it.
    final_reasoning = _extract_reasoning_from_ai_message(response)
    if final_reasoning:
        response.additional_kwargs["reasoning"] = final_reasoning

    # Emit tool_call custom events so the SSE route can forward them to the frontend
    for tc in getattr(response, "tool_calls", []) or []:
        writer({
            "type": "tool_call",
            "name": tc.get("name", ""),
            "args": tc.get("args", {}),
            "id": tc.get("id", ""),
        })

    return {"messages": [response]}

# ─── Routing ──────────────────────────────────────────────────────────────────

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Route to tools if the model emitted a tool call, otherwise END."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

# ─── Graph builder ────────────────────────────────────────────────────────────

def _build_graph(checkpointer: AsyncPostgresSaver) -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)  # custom wrapper emits tool_result events
    graph.add_edge(START, "agent")  # replaces deprecated set_entry_point
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)

# ─── Public: lazily initialised compiled graph ────────────────────────────────

_graph = None
_pool = None


async def get_graph() -> Any:
    """
    Initialise the Postgres connection pool and LangGraph checkpointer on first call.

    Pool kwargs MUST include:
      autocommit=True  — required by AsyncPostgresSaver for all operations
      row_factory=dict_row — required so rows are read as dicts, not tuples
    This also means setup() no longer needs a separate autocommit connection.
    """
    global _graph, _pool
    if _graph is None:
        from psycopg_pool import AsyncConnectionPool

        conn_string = _psycopg_url(POSTGRES_URL)
        _pool = AsyncConnectionPool(
            conninfo=conn_string,
            max_size=10,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
            },
            open=False,
        )
        await _pool.open()
        checkpointer = AsyncPostgresSaver(_pool)
        await checkpointer.setup()
        _graph = _build_graph(checkpointer)
    return _graph


async def close_graph() -> None:
    """Close the Postgres connection pool cleanly on app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

