# Pedagogical Agent

This document explains how the pedagogical agent works end-to-end: lesson embedding, RAG retrieval, streaming behavior, and reasoning-memory preservation.

## What this agent does

- Uses a LangGraph loop: `agent -> tools -> agent` until no tool calls remain.
- Uses two tools:
  - `rewrite_query`: optional query cleanup for retrieval quality.
  - `rag_retrieve`: semantic retrieval over embedded lesson pages.
- Streams server events to frontend via FastAPI SSE:
  - `thinking`
  - `content`
  - `tool_call`
  - `tool_result`
  - `done`
  - `error`

## Core files

- `backend/agents/pedagogical_agent/agent.py`
  - Graph definition
  - LLM wrapper
  - Reasoning preservation in message history
- `backend/agents/pedagogical_agent/tools.py`
  - Query rewriting
  - RAG retrieval + page image packaging
- `backend/server/routes/agents_route.py`
  - `/agents/pedagogical` SSE endpoint
  - Reasoning/content event emission
- `backend/agents/pedagogical_agent/test_agent.py`
  - Raw SSE dump utility for endpoint diagnostics

## Lesson upload -> embedding -> retrieval flow

1. A lesson/file is uploaded and embedded.
2. The resulting vectors are stored in the vector store with a `doc_id` (upload id).
3. During chat, frontend sends selected `file_ids`.
4. Agent receives `doc_ids=file_ids` in graph state.
5. If retrieval is needed, agent calls `rag_retrieve(query, doc_ids, max_px)`.
6. `rag_retrieve`:
   - embeds the query (`embed_query`),
   - applies a `doc_id` filter,
   - runs semantic search,
   - returns relevant page payloads (image/base64 + source metadata).

## Streaming behavior (important)

The provider sends reasoning and answer in separate phases.

Observed raw SSE shape (OpenAI-compatible endpoint):

- Reasoning phase tokens arrive as `delta.reasoning`.
- Final answer tokens arrive as `delta.content`.

Agent behavior:

- `agent.py` captures streamed `delta.reasoning` and exposes it in chunk metadata.
- `agents_route.py` emits:
  - `event: thinking` for reasoning tokens,
  - `event: content` for answer tokens.
- If a model embeds `<think>...</think>` inside `content`, route still supports fallback splitting.

## Reasoning key policy

Canonical key used across this agent: `reasoning`.

Why:

- Raw endpoint stream currently emits `delta.reasoning`.
- Some ecosystems still use `reasoning_content` for compatibility.
- This agent reads both, but writes/sends canonical `reasoning` when possible.

## Memory and checkpoint behavior

The graph uses Postgres checkpointer (`thread_id`-scoped session memory).

What is stored and replayed:

- User/assistant/tool messages are checkpointed by LangGraph.
- Assistant final `content` is replayed each turn.
- Assistant `reasoning` is also preserved and resent in history in this project.

How reasoning is preserved here:

1. During generation, reasoning stream is captured.
2. Final assistant message stores reasoning in `additional_kwargs["reasoning"]`.
3. Next turn, outgoing assistant history includes top-level message key:
   - `{"role":"assistant","content":"...","reasoning":"..."}`

This is the key expected by the current Qwen/vLLM stream behavior in this project.

## Thinking controls

Request-level controls are sent in `extra_body`:

- `think`: bool
- `chat_template_kwargs.enable_thinking`: bool
- `chat_template_kwargs.preserve_thinking`: bool

Current defaults in agent:

- `preserve_thinking=True`
- `enable_thinking` follows incoming request `reasoning` flag.

## Diagnostics

### 1) Raw endpoint SSE dump (bypasses LangChain)

Use this when debugging provider fields and parser behavior.

```powershell
cd C:\Users\Dusty\PycharmProjects\Digi-School
python backend\agents\pedagogical_agent\test_agent.py --thinking on --prompt "Solve 23*17 step by step" --output dump_rawsse_think_on.txt
```

### 2) Route stream diagnostics

`/agents/pedagogical` logs a summary line at stream end with chunk counts:

- `thinking_chunks`
- `content_chunks`

Use this to verify phase transition in real requests.

## Expected SSE timeline to frontend

Typical sequence:

1. many `thinking` events
2. then many `content` events
3. finally `done`

Tool events may appear between turns as `tool_call` / `tool_result`.

## Caveats

- If a model returns incorrect reasoning, preserving it may reinforce that logic on later turns.
- For recovery, create a new session/thread or clear history.
- Behavior depends on serving/parser versions; keep raw SSE dump tests available after upgrades.

## Quick operational checklist

- Ensure uploaded files are embedded before querying.
- Pass correct `file_ids` in `/agents/pedagogical` request.
- Set `reasoning=true` to enable thinking stream.
- Confirm frontend listens to named SSE events (`thinking`, `content`, `done`, `error`).
- If behavior changes after upgrades, run raw SSE dump first.

