"""
Agents route — session management + pedagogical agent SSE streaming endpoint.
"""
import json
import logging
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlmodel import Session, select

from backend.models import AppError
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import AgentSession
from backend.classes.access import get_owned_class_or_403

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    class_id: int
    title: str = Field(..., min_length=1, max_length=120)


class AgentRequest(BaseModel):
    thread_id: str
    file_ids: List[str] = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    reasoning: bool = False


# ─── Session management ───────────────────────────────────────────────────────

@router.post("/sessions")
def create_session(
    body: CreateSessionRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """Create a new named agent session for a class."""
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=body.class_id)

    agent_session = AgentSession(
        teacher_id=teacher_id,
        class_id=body.class_id,
        title=body.title.strip(),
    )
    session.add(agent_session)
    session.commit()
    session.refresh(agent_session)

    return {
        "success": True,
        "session": _serialize_session(agent_session),
    }


@router.get("/sessions")
def list_sessions(
    class_id: int = Query(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """List all agent sessions for a class, newest first."""
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    rows = session.exec(
        select(AgentSession)
        .where(
            AgentSession.teacher_id == teacher_id,
            AgentSession.class_id == class_id,
        )
        .order_by(desc(AgentSession.created_at))
    ).all()

    return {
        "success": True,
        "sessions": [_serialize_session(r) for r in rows],
    }


@router.get("/sessions/{thread_id}")
def get_session_detail(
    thread_id: str,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """Get metadata for a single session."""
    teacher_id = int(teacher["id"])
    agent_session = _get_owned_session_or_404(session, thread_id, teacher_id)
    return {"success": True, "session": _serialize_session(agent_session)}


@router.delete("/sessions/{thread_id}")
def delete_session(
    thread_id: str,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """Delete a session and its metadata."""
    teacher_id = int(teacher["id"])
    agent_session = _get_owned_session_or_404(session, thread_id, teacher_id)
    session.delete(agent_session)
    session.commit()
    return {"success": True, "deleted": thread_id}


# ─── Agent invoke — SSE streaming ────────────────────────────────────────────

@router.post("/pedagogical")
async def pedagogical_agent(
    body: AgentRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Streaming SSE endpoint for the pedagogical agent.
    Uses graph.astream(stream_mode=["messages","custom"]):
      - "messages" mode → per-token AIMessageChunk for thinking/content split
      - "custom" mode   → tool_call/tool_result events from get_stream_writer()

    SSE event types:
      event: thinking    — <think> token chunks
      event: content     — answer token chunks
      event: tool_call   — tool invocation notification
      event: tool_result — rewrite_query result
      event: error       — fatal error
      event: done        — stream finished
    """
    from backend.server.db.dbModels import Upload
    from backend.agents.pedagogical_agent.agent import get_graph

    teacher_id = int(teacher["id"])
    _get_owned_session_or_404(session, body.thread_id, teacher_id)

    for fid in body.file_ids:
        upload = session.get(Upload, fid)
        if upload is None:
            raise AppError("AGENT_FILE_NOT_FOUND", f"File {fid} not found.", 404)
        if not upload.embedded:
            raise AppError(
                "AGENT_FILE_NOT_EMBEDDED",
                f"File '{upload.filename}' is not yet embedded. Please wait or retry.",
                422,
            )
        get_owned_class_or_403(session, teacher_id=teacher_id, class_id=upload.class_id)

    async def event_stream() -> AsyncIterator[str]:
        try:
            from langchain_core.messages import HumanMessage

            graph = await get_graph()
            config = {"configurable": {"thread_id": body.thread_id}}
            input_state = {
                "messages": [HumanMessage(content=body.prompt)],
                "doc_ids": body.file_ids,
                "reasoning": body.reasoning,
            }

            in_think = False
            saw_reasoning = False
            saw_content = False
            thinking_chunks = 0
            content_chunks = 0

            async for stream_mode, chunk in graph.astream(
                input_state,
                config=config,
                stream_mode=["messages", "custom"],
            ):
                # ── Per-token LLM output ───────────────────────────────────
                if stream_mode == "messages":
                    msg_chunk, metadata = chunk

                    # Preferred path: reasoning tokens surfaced separately from content
                    reasoning_tok = _extract_reasoning_tokens(msg_chunk)
                    # Snapshot BEFORE mutating the flag so a transition chunk (reasoning +
                    # content in the same delta) doesn't immediately route its own content
                    # token as an answer — that would permanently close the thinking path.
                    already_saw_reasoning = saw_reasoning
                    if reasoning_tok and not saw_content:
                        saw_reasoning = True
                        thinking_chunks += 1
                        yield _sse("thinking", reasoning_tok)

                    raw = msg_chunk.content if isinstance(msg_chunk.content, str) else ""
                    if not raw:
                        continue

                    # Only use the fast-path if reasoning was already established on a
                    # *previous* chunk (use snapshot). If both appeared in the same chunk
                    # fall through to the <think>-tag parser which handles it correctly.
                    if already_saw_reasoning:
                        saw_content = True
                        content_chunks += 1
                        yield _sse("content", raw)
                        continue

                    # Fallback path for models that embed <think> tags directly in content.
                    buf = raw
                    while buf:
                        if not in_think:
                            idx = buf.find("<think>")
                            if idx == -1:
                                saw_content = True
                                content_chunks += 1
                                yield _sse("content", buf)
                                break
                            before = buf[:idx]
                            if before:
                                saw_content = True
                                content_chunks += 1
                                yield _sse("content", before)
                            buf = buf[idx + len("<think>"):]
                            in_think = True
                        else:
                            idx = buf.find("</think>")
                            if idx == -1:
                                saw_reasoning = True
                                thinking_chunks += 1
                                yield _sse("thinking", buf)
                                break
                            if buf[:idx]:
                                saw_reasoning = True
                                thinking_chunks += 1
                                yield _sse("thinking", buf[:idx])
                            buf = buf[idx + len("</think>"):]
                            in_think = False

                # ── Custom events from get_stream_writer() in agent_node ───
                elif stream_mode == "custom":
                    if isinstance(chunk, dict):
                        event_type = chunk.get("type", "custom")
                        yield _sse(event_type, json.dumps(chunk))

            logger.info(
                "pedagogical_stream thread_id=%s reasoning=%s thinking_chunks=%d content_chunks=%d",
                body.thread_id,
                body.reasoning,
                thinking_chunks,
                content_chunks,
            )
            yield _sse("done", "")

        except Exception as exc:
            yield _sse("error", str(exc))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _serialize_session(s: AgentSession) -> Dict[str, Any]:
    return {
        "thread_id": s.thread_id,
        "class_id": s.class_id,
        "title": s.title,
        "created_at": s.created_at,
    }


def _get_owned_session_or_404(session: Session, thread_id: str, teacher_id: int) -> AgentSession:
    agent_session = session.get(AgentSession, thread_id)
    if agent_session is None:
        raise AppError("AGENT_SESSION_NOT_FOUND", "Session not found.", 404)
    if agent_session.teacher_id != teacher_id:
        raise AppError("AGENT_SESSION_FORBIDDEN", "Access denied.", 403)
    return agent_session


def _sse(event: str, data: str) -> str:
    """Format a single SSE frame."""
    return f"event: {event}\ndata: {data}\n\n"


# ─── Stream token helpers ─────────────────────────────────────────────────────

def _extract_reasoning_tokens(msg_chunk: Any) -> str:
    """Extract provider-normalized reasoning tokens from a streamed message chunk."""
    out = ""

    # 1) Legacy/adapter path: additional_kwargs
    # Read only one key — agent sets both "reasoning" and "reasoning_content" to the same
    # value, so iterating both would double every token.
    additional = getattr(msg_chunk, "additional_kwargs", None)
    if isinstance(additional, dict):
        val = additional.get("reasoning") or additional.get("reasoning_content")
        if isinstance(val, str):
            out += val

    # 2) New LangChain path: content_blocks / content_blocks-like entries
    blocks = getattr(msg_chunk, "content_blocks", None)
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
