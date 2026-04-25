"""
backend/server/routes/creator_route.py
---------------------------------------
REST + SSE endpoints for the Creator Agent — AI exam generator.

════ ENDPOINTS ════
  POST   /agents/creator/generate                start or resume exam generation (SSE)
  GET    /agents/creator/sessions                list teacher's exam sessions
  GET    /agents/creator/sessions/{id}           get session details + exam_json
  DELETE /agents/creator/sessions/{id}           delete session + LangGraph checkpoint
  POST   /agents/creator/retry-overview          re-queue overview for overview IS NULL uploads

SSE events (generate):
  thinking           — reasoning chunk (if reasoning=true)
  content            — agent narrative chunk
  tool_call          — {"type","name","args","id"}
  tool_result        — {"type","name","content","tool_call_id"} (get_doc_overviews only)
  evaluator_feedback — {"flagged":[...],"loop_count":int}
  exam_draft         — {"questions":[...]} draft produced by creator
  exam_saved         — {"session_id":int,"title":"...","loop_count":int}
  error              — error string
  done               — stream finished
"""
import json
import logging
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlmodel import Session, select

from backend.models import AppError
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import GeneratedExam, Upload
from backend.config import POSTGRES_URL

router = APIRouter(prefix="/agents/creator", tags=["creator-agent"])
logger = logging.getLogger(__name__)


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class ExamPreferences(BaseModel):
    topics: List[str] = Field(default_factory=list)
    difficulty_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"easy": 30, "medium": 50, "hard": 20}
    )
    exercise_types: List[str] = Field(default_factory=lambda: ["mcq", "open"])
    question_count: int = Field(default=10, ge=1, le=50)
    total_points: float = Field(default=20.0, gt=0)
    language: str = Field(default="French", max_length=50)
    notes: str = Field(default="", max_length=1000)


class GenerateRequest(BaseModel):
    session_id: Optional[int] = None       # null = new session, int = resume existing
    doc_ids: List[str] = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    preferences: ExamPreferences = Field(default_factory=ExamPreferences)
    prompt: str = Field(default="Generate the exam based on the preferences.")
    reasoning: bool = False


class RetryOverviewRequest(BaseModel):
    class_id: int


# ─── SSE helpers ──────────────────────────────────────────────────────────────

def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def _extract_reasoning_tokens(msg_chunk: Any) -> str:
    out = ""
    additional = getattr(msg_chunk, "additional_kwargs", None)
    if isinstance(additional, dict):
        val = additional.get("reasoning") or additional.get("reasoning_content")
        if isinstance(val, str):
            out += val
    blocks = getattr(msg_chunk, "content_blocks", None)
    if isinstance(blocks, list):
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                val = block.get("reasoning") or block.get("text")
                if isinstance(val, str):
                    out += val
    return out


async def _stream_graph(graph: Any, input_data: Any, config: dict) -> AsyncIterator[str]:
    """
    Unified SSE streaming helper for the creator graph.
    Handles thinking/content split and all custom events.
    """
    in_think = False
    saw_reasoning = False
    saw_content = False

    async for stream_mode, chunk in graph.astream(
        input_data,
        config=config,
        stream_mode=["messages", "custom"],
    ):
        # ── Per-token LLM output ──────────────────────────────────────────────
        if stream_mode == "messages":
            msg_chunk, _metadata = chunk

            reasoning_tok = _extract_reasoning_tokens(msg_chunk)
            already_saw_reasoning = saw_reasoning
            if reasoning_tok and not saw_content:
                saw_reasoning = True
                yield _sse("thinking", reasoning_tok)

            raw = msg_chunk.content if isinstance(msg_chunk.content, str) else ""
            if not raw:
                continue

            if already_saw_reasoning:
                saw_content = True
                yield _sse("content", raw)
                continue

            # Fallback: parse inline <think>…</think> tags
            buf = raw
            while buf:
                if not in_think:
                    idx = buf.find("<think>")
                    if idx == -1:
                        saw_content = True
                        yield _sse("content", buf)
                        break
                    if idx > 0:
                        saw_content = True
                        yield _sse("content", buf[:idx])
                    in_think = True
                    buf = buf[idx + len("<think>"):]
                else:
                    idx = buf.find("</think>")
                    if idx == -1:
                        saw_reasoning = True
                        yield _sse("thinking", buf)
                        break
                    if idx > 0:
                        saw_reasoning = True
                        yield _sse("thinking", buf[:idx])
                    in_think = False
                    buf = buf[idx + len("</think>"):]

        # ── Custom events from get_stream_writer() ────────────────────────────
        elif stream_mode == "custom":
            event_type = chunk.get("type", "")

            if event_type == "tool_call":
                yield _sse("tool_call", json.dumps({
                    "type": "tool_call",
                    "name": chunk.get("name", ""),
                    "args": chunk.get("args", {}),
                    "id": chunk.get("id", ""),
                }))

            elif event_type == "tool_result":
                yield _sse("tool_result", json.dumps({
                    "type": "tool_result",
                    "name": chunk.get("name", ""),
                    "content": chunk.get("content", ""),
                    "tool_call_id": chunk.get("tool_call_id", ""),
                }))

            elif event_type == "exam_draft":
                yield _sse("exam_draft", json.dumps({
                    "questions": chunk.get("questions", []),
                }))

            elif event_type == "evaluator_feedback":
                yield _sse("evaluator_feedback", json.dumps({
                    "flagged": chunk.get("flagged", []),
                    "loop_count": chunk.get("loop_count", 1),
                }))


# ─── POST /agents/creator/generate ───────────────────────────────────────────

@router.post("/generate")
async def generate_exam(
    body: GenerateRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    db: Session = Depends(get_session),
):
    """
    Start or resume an exam generation session. Returns an SSE stream.

    - session_id = null  → creates a new GeneratedExam session
    - session_id = int   → resumes an existing session (teacher refinement)
    """
    teacher_id = int(teacher["id"])

    # ── Validate doc_ids ──────────────────────────────────────────────────────
    not_embedded = []
    for doc_id in body.doc_ids:
        upload = db.get(Upload, doc_id)
        if upload is None:
            raise AppError("CREATOR_DOC_NOT_FOUND", f"Upload {doc_id} not found.", 404)
        if not upload.embedded:
            not_embedded.append(doc_id)
    if not_embedded:
        raise AppError(
            "CREATOR_DOC_NOT_EMBEDDED",
            f"Documents not yet embedded: {not_embedded}. Wait for embedding to complete.",
            400,
        )

    # ── Resolve or create GeneratedExam row ───────────────────────────────────
    if body.session_id is not None:
        exam_row = db.get(GeneratedExam, body.session_id)
        if exam_row is None or exam_row.teacher_id != teacher_id:
            raise AppError("CREATOR_SESSION_NOT_FOUND", "Session not found.", 404)
        thread_id = exam_row.thread_id
    else:
        thread_id = str(uuid.uuid4())
        exam_row = GeneratedExam(
            teacher_id=teacher_id,
            thread_id=thread_id,
            title=body.title.strip(),
            doc_ids=json.dumps(body.doc_ids),
            preferences=body.preferences.model_dump_json(),
        )
        db.add(exam_row)
        db.commit()
        db.refresh(exam_row)

    session_id = exam_row.id
    title = exam_row.title

    # ── Warn about missing overviews (non-fatal) ──────────────────────────────
    missing_overviews = []
    for doc_id in body.doc_ids:
        upload = db.get(Upload, doc_id)
        if upload and upload.overview is None:
            missing_overviews.append(doc_id)

    # Build LangGraph config
    config = {"configurable": {"thread_id": thread_id}}

    # Build initial state (for new session) or just a follow-up human message (resume)
    from langchain_core.messages import HumanMessage as LCHumanMessage
    from backend.agents.creator_agent.agent import get_graph

    if body.session_id is None:
        # New session: full state initialisation
        initial_state = {
            "messages": [LCHumanMessage(content=body.prompt)],
            "doc_ids": body.doc_ids,
            "preferences": body.preferences.model_dump(),
            "reasoning": body.reasoning,
            "loop_count": 0,
            "exam_draft": None,
            "evaluator_feedback": None,
        }
        if missing_overviews:
            initial_state["messages"] = [
                LCHumanMessage(content=(
                    f"{body.prompt}\n\n"
                    f"NOTE: The following documents have no pre-generated overview yet "
                    f"(overview_ready=false): {missing_overviews}. "
                    f"Call get_doc_overviews anyway — it will return null overview fields. "
                    f"Proceed using rag_retrieve for those documents."
                ))
            ]
        input_data = initial_state
    else:
        # Resume: add the teacher's new message to existing checkpoint
        input_data = {"messages": [LCHumanMessage(content=body.prompt)]}

    async def event_stream() -> AsyncIterator[str]:
        try:
            graph = await get_graph()
            async for sse_chunk in _stream_graph(graph, input_data, config):
                yield sse_chunk

            # ── After stream completes: persist final exam_json to DB ─────────
            try:
                # Read final state from checkpoint
                final_state = await graph.aget_state(config)
                exam_draft = final_state.values.get("exam_draft")
                loop_count = final_state.values.get("loop_count", 0)

                if exam_draft:
                    from sqlmodel import Session as SyncSession, create_engine
                    engine = create_engine(POSTGRES_URL, echo=False)
                    with SyncSession(engine) as sync_db:
                        row = sync_db.get(GeneratedExam, session_id)
                        if row:
                            row.exam_json = json.dumps(exam_draft)
                            row.loop_count = loop_count
                            sync_db.add(row)
                            sync_db.commit()
                    engine.dispose()

                    yield _sse("exam_saved", json.dumps({
                        "session_id": session_id,
                        "title": title,
                        "loop_count": loop_count,
                    }))
            except Exception as save_exc:
                logger.error("Failed to persist exam_json for session %s: %s", session_id, save_exc)

            yield _sse("done", "")

        except Exception as exc:
            logger.error("Creator stream error (session %s): %s", session_id, exc)
            yield _sse("error", str(exc))
            yield _sse("done", "")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── GET /agents/creator/sessions ────────────────────────────────────────────

@router.get("/sessions")
def list_exam_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    teacher: Dict[str, Any] = Depends(require_auth),
    db: Session = Depends(get_session),
):
    """List the teacher's exam generation sessions, newest first."""
    teacher_id = int(teacher["id"])

    rows = db.exec(
        select(GeneratedExam)
        .where(GeneratedExam.teacher_id == teacher_id)
        .order_by(desc(GeneratedExam.created_at))
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "success": True,
        "sessions": [
            {
                "session_id": r.id,
                "title": r.title,
                "doc_ids": json.loads(r.doc_ids) if r.doc_ids else [],
                "loop_count": r.loop_count,
                "has_exam": bool(r.exam_json),
                "created_at": r.created_at,
            }
            for r in rows
        ],
        "pagination": {"limit": limit, "offset": offset},
    }


# ─── GET /agents/creator/sessions/{id} ───────────────────────────────────────

@router.get("/sessions/{session_id}")
def get_exam_session(
    session_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    db: Session = Depends(get_session),
):
    """Get a single exam session including the full exam_json."""
    teacher_id = int(teacher["id"])
    row = db.get(GeneratedExam, session_id)

    if row is None or row.teacher_id != teacher_id:
        raise AppError("CREATOR_SESSION_NOT_FOUND", "Session not found.", 404)

    exam = None
    if row.exam_json:
        try:
            exam = json.loads(row.exam_json)
        except json.JSONDecodeError:
            exam = None

    return {
        "success": True,
        "session": {
            "session_id": row.id,
            "title": row.title,
            "doc_ids": json.loads(row.doc_ids) if row.doc_ids else [],
            "preferences": json.loads(row.preferences) if row.preferences else {},
            "exam": exam,
            "loop_count": row.loop_count,
            "created_at": row.created_at,
        },
    }


# ─── DELETE /agents/creator/sessions/{id} ────────────────────────────────────

@router.delete("/sessions/{session_id}")
async def delete_exam_session(
    session_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    db: Session = Depends(get_session),
):
    """Delete a session row and its LangGraph checkpoint."""
    teacher_id = int(teacher["id"])
    row = db.get(GeneratedExam, session_id)

    if row is None or row.teacher_id != teacher_id:
        raise AppError("CREATOR_SESSION_NOT_FOUND", "Session not found.", 404)

    thread_id = row.thread_id

    # ── Hard-delete LangGraph checkpoint ─────────────────────────────────────
    try:
        from backend.agents.db import get_checkpointer
        checkpointer = await get_checkpointer()
        config = {"configurable": {"thread_id": thread_id}}
        await checkpointer.adelete_thread(thread_id)
    except Exception as exc:
        logger.warning("Could not delete LangGraph checkpoint for thread %s: %s", thread_id, exc)

    db.delete(row)
    db.commit()

    return {"success": True, "deleted": {"session_id": session_id, "title": row.title}}


# ─── POST /agents/creator/retry-overview ─────────────────────────────────────

@router.post("/retry-overview")
def retry_overview(
    body: RetryOverviewRequest,
    background_tasks: BackgroundTasks,
    teacher: Dict[str, Any] = Depends(require_auth),
    db: Session = Depends(get_session),
):
    """
    Re-queue overview generation for all uploads in a class where overview IS NULL.
    Same pattern as POST /lessons/retry-embed.
    """
    from backend.classes.access import get_owned_class_or_403
    from backend.agents.creator_agent.preprocessor import generate_overview_task
    from pathlib import Path

    teacher_id = int(teacher["id"])
    get_owned_class_or_403(db, teacher_id=teacher_id, class_id=body.class_id)

    uploads = db.exec(
        select(Upload).where(
            Upload.class_id == body.class_id,
            Upload.overview == None,  # noqa: E711 — SQLAlchemy IS NULL
            Upload.embedded == True,  # noqa: E712
        )
    ).all()

    _BASE_DIR = Path(__file__).resolve().parents[3]
    queued: List[str] = []

    for upload in uploads:
        abs_path = str(_BASE_DIR / upload.file_path)
        if Path(abs_path).exists():
            background_tasks.add_task(
                generate_overview_task,
                file_path=abs_path,
                upload_id=upload.id,
                db_url=POSTGRES_URL,
            )
            queued.append(upload.id)
        else:
            logger.warning("retry-overview: file missing for upload %s", upload.id)

    return {"success": True, "queued": queued}

