"""
backend/server/routes/grading_route.py
----------------------------------------
REST + SSE endpoints for the two-phase grading agent.

The blueprint is NOT a JSON column — it is the suspended LangGraph checkpoint
after the agent has processed the exam paper, correction, and lesson RAG.
Each student grading session forks that checkpoint (SQL copy) so the agent
already knows the exam and only needs to read the one student's paper.

════ EXAM PAPERS (class-scoped, uploaded before analysis) ════
  POST   /agents/grading/exam-papers               upload exam question paper
  GET    /agents/grading/exam-papers?class_id=     list papers for a class
  DELETE /agents/grading/exam-papers/{id}          smart delete (checks other classes)

════ BLUEPRINTS (teacher-scoped, Phase 1) ════
  POST   /agents/grading/analyse                   create blueprint — SSE stream
  GET    /agents/grading/blueprints                list teacher's blueprints
  GET    /agents/grading/blueprints/{id}           get single blueprint
  DELETE /agents/grading/blueprints/{id}           soft-delete + hard-delete checkpoint

════ GRADING SESSIONS (Phase 2) ════
  POST   /agents/grading/grade                     create ordered batch of sessions
  GET    /agents/grading/sessions                  list sessions (filter batch/class/blueprint)
  GET    /agents/grading/sessions/{id}/stream      SSE: grade one student
  POST   /agents/grading/sessions/{id}/review      approve/edit/cancel → returns next_session_id

SSE events (both /analyse and /sessions/{id}/stream):
  thinking        — reasoning chunk (if reasoning=true)
  content         — agent narrative chunk
  tool_call       — {"type","name","args","id"}
  tool_result     — {"type","name","content","tool_call_id"}
  blueprint_ready — {} graph suspended; blueprint checkpoint saved
  blueprint_saved — {"blueprint_id": int, "title": str}
  question_result — {"question_number","label","max_points","awarded_points","reasoning"}
  interrupt       — {"breakdown":[...]}  → teacher POSTs /review
  error           — error string
  done            — stream finished
"""
import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.models import AppError
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import (
    ExamPaper, ExamType, ExamUpload, GradingBlueprint, GradingQuestionResult,
    GradingSession, StudentClass, Upload,
)
from backend.classes.access import get_owned_class_or_403

router = APIRouter(prefix="/agents/grading", tags=["grading-agent"])
logger = logging.getLogger(__name__)


# ─── Storage paths ────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parents[3]
_EXAM_PAPERS_DIR  = _BASE_DIR / "uploads" / "exam_papers"
_EXAM_UPLOADS_DIR = _BASE_DIR / "uploads" / "exams"


def _exam_papers_dir(teacher_id: int) -> Path:
    p = _EXAM_PAPERS_DIR / str(teacher_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _exam_uploads_dir(teacher_id: int) -> Path:
    p = _EXAM_UPLOADS_DIR / str(teacher_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _corrections_dir(teacher_id: int) -> Path:
    p = _EXAM_UPLOADS_DIR / str(teacher_id) / "corrections"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


async def _stream_graph(graph: Any, input_or_command: Any, config: dict) -> AsyncIterator[str]:
    """
    Shared SSE streaming helper for the grading graph.
    Works for both blueprint phase (state dict) and grading phase (Command resume).
    Handles thinking/content token split + all custom events from get_stream_writer().
    """
    in_think = False
    saw_reasoning = False
    saw_content = False

    async for stream_mode, chunk in graph.astream(
        input_or_command,
        config=config,
        stream_mode=["messages", "custom"],
    ):
        # ── Per-token LLM output ──────────────────────────────────────────
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

            # Fast-path: reasoning was established on a prior chunk
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
                    before = buf[:idx]
                    if before:
                        saw_content = True
                        yield _sse("content", before)
                    buf = buf[idx + len("<think>"):]
                    in_think = True
                else:
                    idx = buf.find("</think>")
                    if idx == -1:
                        saw_reasoning = True
                        yield _sse("thinking", buf)
                        break
                    if buf[:idx]:
                        saw_reasoning = True
                        yield _sse("thinking", buf[:idx])
                    buf = buf[idx + len("</think>"):]
                    in_think = False

        # ── Custom events from get_stream_writer() in agent nodes ─────────
        elif stream_mode == "custom":
            if isinstance(chunk, dict):
                event_type = chunk.get("type", "custom")
                yield _sse(event_type, json.dumps(chunk))


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class QuestionDecision(BaseModel):
    question_number: int
    awarded_points: float


class ReviewRequest(BaseModel):
    decisions: List[QuestionDecision]
    action: str = Field(..., pattern="^(approve|cancel)$")


# ══════════════════════════════════════════════════════════════════════════════
#  EXAM PAPERS  (class-scoped)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/exam-papers")
async def upload_exam_paper(
    class_id: int = Form(...),
    file: UploadFile = File(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Upload an exam question paper PDF for a class.
    Deduplicates by (class_id, sha256): returns existing row if duplicate.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise AppError("GRADING_INVALID_FILE", "Only PDF files are accepted.", 400)

    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    data = await file.read()
    file_hash = _sha256(data)

    existing = session.exec(
        select(ExamPaper).where(
            ExamPaper.class_id == class_id,
            ExamPaper.file_hash == file_hash,
        )
    ).first()
    if existing:
        return {"success": True, "exam_paper": _serialize_exam_paper(existing), "duplicate": True}  # type: ignore[arg-type]

    dest = _exam_papers_dir(teacher_id) / f"{uuid.uuid4()}.pdf"
    dest.write_bytes(data)

    row = ExamPaper(
        class_id=class_id,
        teacher_id=teacher_id,
        filename=file.filename,
        file_path=str(dest),
        file_hash=file_hash,
        size=len(data),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return {"success": True, "exam_paper": _serialize_exam_paper(row), "duplicate": False}


@router.get("/exam-papers")
def list_exam_papers(
    class_id: int = Query(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """List all exam papers for a class."""
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    rows = session.exec(
        select(ExamPaper).where(ExamPaper.class_id == class_id)
    ).all()
    return {"success": True, "exam_papers": [_serialize_exam_paper(r) for r in rows]}


@router.delete("/exam-papers/{paper_id}")
def delete_exam_paper(
    paper_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Delete an exam paper row.
    Only unlinks the file from disk if no other ExamPaper row references the same
    file_hash — handles teachers who assign the same exam to multiple classes.
    """
    teacher_id = int(teacher["id"])
    paper = _get_owned_exam_paper_or_404(session, paper_id, teacher_id)

    other_refs = session.exec(
        select(ExamPaper).where(
            ExamPaper.file_hash == paper.file_hash,
            ExamPaper.id != paper.id,
        )
    ).first()

    if other_refs is None:
        try:
            Path(paper.file_path).unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Could not delete exam paper file %s: %s", paper.file_path, exc)

    session.delete(paper)
    session.commit()
    return {"success": True, "deleted": paper_id}


# ══════════════════════════════════════════════════════════════════════════════
#  BLUEPRINT  --  Phase 1 (/analyse)
# ══════════════════════════════════════════════════════════════════════════════
class AnalyseRequest(BaseModel):
    exam_paper_id: int
    lesson_file_ids: list[str] = []
    preferences: str = ""
    style_guide: str = ""
    title: str
    reasoning: bool = False

@router.post("/analyse")
async def analyse_blueprint(
    exam_paper_id: int = Form(...),
    correction_pdf: Optional[UploadFile] = File(None),
    lesson_file_ids: str = Form("[]"),
    preferences: str = Form(""),
    style_guide: str = Form(""),
    title: str = Form(...),
    reasoning: bool = Form(False),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Phase 1 — Analyse exam paper and build the correction blueprint.

    Takes an exam_paper_id (already uploaded via POST /exam-papers).
    Correction PDF is optional and is DELETED from disk after analysis.
    Lesson doc IDs are used for RAG (must already be embedded).

    SSE events: thinking, content, tool_call, tool_result,
                blueprint_ready, blueprint_saved {"blueprint_id","title"}, error, done
    """
    teacher_id = int(teacher["id"])

    paper = _get_owned_exam_paper_or_404(session, exam_paper_id, teacher_id)

    try:
        doc_ids: List[str] = json.loads(lesson_file_ids)
        if not isinstance(doc_ids, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        doc_ids = [item.strip() for item in lesson_file_ids.split(",") if item.strip()]
    if not isinstance(doc_ids, list):
        raise AppError(
            "GRADING_INVALID_PARAMS",
            "lesson_file_ids must be a JSON array or a comma-separated list of IDs.",
            400
        )

    for fid in doc_ids:
        upload = session.get(Upload, fid)
        if upload is None:
            raise AppError("GRADING_FILE_NOT_FOUND", f"Lesson file {fid} not found.", 404)
        if not upload.embedded:
            raise AppError(
                "GRADING_FILE_NOT_EMBEDDED",
                f"Lesson file '{upload.filename}' is not yet embedded.", 422,
            )

    # Save correction PDF temporarily (deleted after analysis)
    correction_path_str: Optional[str] = None
    if correction_pdf and correction_pdf.filename:
        if not correction_pdf.filename.lower().endswith(".pdf"):
            raise AppError("GRADING_INVALID_FILE", "correction_pdf must be a PDF.", 400)
        corr_data = await correction_pdf.read()
        corr_path = _corrections_dir(teacher_id) / f"{uuid.uuid4()}.pdf"
        corr_path.write_bytes(corr_data)
        correction_path_str = str(corr_path)

    analysis_thread_id = str(uuid.uuid4())
    exam_file_path = paper.file_path

    async def event_stream() -> AsyncIterator[str]:
        from backend.agents.grading_agent.agent import get_grading_graph
        from langchain_core.messages import HumanMessage

        try:
            graph = await get_grading_graph()
            config = {"configurable": {"thread_id": analysis_thread_id}}
            input_state = {
                "messages": [HumanMessage(content="Analyse this exam and build your understanding.")],
                "lesson_doc_ids": doc_ids,
                "exam_file_path": exam_file_path,
                "correction_file_path": correction_path_str,
                "preferences": preferences,
                "style_guide": style_guide,
                "reasoning": reasoning,
                "student_exam_path": "",
                "breakdown": [],
                "teacher_decisions": {},
            }

            async for sse_frame in _stream_graph(graph, input_state, config):
                yield sse_frame

            # Graph suspended at bp_interrupt_node — checkpoint IS the blueprint
            bp = GradingBlueprint(
                teacher_id=teacher_id,
                title=title.strip(),
                analysis_thread_id=analysis_thread_id,
                exam_paper_id=exam_paper_id,
                exam_file_path=exam_file_path,
                correction_file_path=None,
                lesson_doc_ids=json.dumps(doc_ids),
                preferences=preferences,
                style_guide=style_guide,
                blueprint_json="",
            )
            session.add(bp)
            session.commit()
            session.refresh(bp)

            # Delete correction PDF — one-time artifact
            if correction_path_str:
                try:
                    Path(correction_path_str).unlink(missing_ok=True)
                except Exception as exc:
                    logger.warning("Could not delete correction PDF %s: %s", correction_path_str, exc)

            yield _sse("blueprint_saved", json.dumps({"blueprint_id": bp.id, "title": bp.title}))
            yield _sse("done", "")

        except Exception as exc:
            logger.exception("Blueprint stream error")
            if correction_path_str:
                try:
                    Path(correction_path_str).unlink(missing_ok=True)
                except Exception:
                    pass
            yield _sse("error", str(exc))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/blueprints")
def list_blueprints(
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    teacher_id = int(teacher["id"])
    rows = session.exec(
        select(GradingBlueprint).where(
            GradingBlueprint.teacher_id == teacher_id,
            GradingBlueprint.deleted == False,  # noqa: E712
        )
    ).all()
    return {"success": True, "blueprints": [_serialize_blueprint(r) for r in rows]}


@router.get("/blueprints/{blueprint_id}")
def get_blueprint(
    blueprint_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    teacher_id = int(teacher["id"])
    bp = _get_owned_blueprint_or_404(session, blueprint_id, teacher_id, allow_deleted=False)
    return {"success": True, "blueprint": _serialize_blueprint(bp)}


@router.delete("/blueprints/{blueprint_id}")
async def delete_blueprint(
    blueprint_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Soft-delete: set deleted=True (metadata row kept).
    Hard-delete the LangGraph checkpoint thread to free Postgres storage.
    Existing student GradingSession checkpoints are NOT deleted.
    """
    teacher_id = int(teacher["id"])
    bp = _get_owned_blueprint_or_404(session, blueprint_id, teacher_id, allow_deleted=True)

    if not bp.deleted:
        if bp.analysis_thread_id:
            try:
                from backend.agents.db import delete_thread
                await delete_thread(bp.analysis_thread_id)
            except Exception as exc:
                logger.warning("Could not delete blueprint checkpoint %s: %s",
                               bp.analysis_thread_id, exc)
        bp.deleted = True
        session.add(bp)
        session.commit()

    return {"success": True, "deleted": blueprint_id}


# ══════════════════════════════════════════════════════════════════════════════
#  GRADING SESSIONS  --  Phase 2
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/grade")
async def start_grading(
    blueprint_id: int = Form(...),
    class_id: int = Form(...),
    exam_type_id: int = Form(...),
    student_ids: List[int] = Form(...),
    exam_pdfs: List[UploadFile] = File(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Create a batch of grading sessions — one per student.

    Accepts multipart/form-data with parallel lists:
      student_ids[] : repeated int  Form field — one per student
      exam_pdfs[]   : repeated PDF  File field — SAME index = same student

    Backend validates enrollment, zips pairs, sorts alphabetically by student name,
    saves PDFs permanently, creates ExamUpload + GradingSession rows with queue_position.

    Returns first_session_id so frontend can immediately open the first stream.
    """
    if len(student_ids) != len(exam_pdfs):
        raise AppError(
            "GRADING_INVALID_PARAMS",
            f"student_ids count ({len(student_ids)}) must match exam_pdfs count ({len(exam_pdfs)}).",
            400,
        )
    if len(student_ids) == 0:
        raise AppError("GRADING_INVALID_PARAMS", "At least one student is required.", 400)
    if len(student_ids) > 20:
        raise AppError("GRADING_INVALID_PARAMS", "Maximum 20 students per batch.", 400)

    teacher_id = int(teacher["id"])

    _get_owned_blueprint_or_404(session, blueprint_id, teacher_id, allow_deleted=False)
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    exam_type = session.exec(
        select(ExamType).where(
            ExamType.id == exam_type_id,
            ExamType.class_id == class_id,
        )
    ).first()
    if exam_type is None:
        raise AppError("GRADING_INVALID_EXAM_TYPE", "exam_type_id not found in this class.", 404)

    # Validate enrollment + collect display names for sorting
    student_names: Dict[int, str] = {}
    for sid in student_ids:
        enrollment = session.exec(
            select(StudentClass).where(
                StudentClass.student_id == sid,
                StudentClass.class_id == class_id,
            )
        ).first()
        if enrollment is None:
            raise AppError(
                "GRADING_STUDENT_NOT_ENROLLED",
                f"Student {sid} is not enrolled in class {class_id}.", 404,
            )
        # Use class-specific display_name (what the teacher sees in their class list)
        student_names[sid] = enrollment.display_name if enrollment.display_name else str(sid)

    # Validate PDFs
    for i, pdf in enumerate(exam_pdfs):
        if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
            raise AppError("GRADING_INVALID_FILE", f"exam_pdfs[{i}] must be a PDF.", 400)

    # Zip + sort alphabetically by student name
    pairs = sorted(zip(student_ids, exam_pdfs), key=lambda p: student_names[p[0]].lower())

    batch_id = str(uuid.uuid4())
    dest_dir = _exam_uploads_dir(teacher_id)
    created = []

    for position, (sid, pdf_file) in enumerate(pairs):
        pdf_data = await pdf_file.read()
        dest_path = dest_dir / f"{uuid.uuid4()}.pdf"
        dest_path.write_bytes(pdf_data)

        exam_upload = ExamUpload(
            teacher_id=teacher_id,
            filename=pdf_file.filename or f"student_{sid}.pdf",
            file_path=str(dest_path),
            file_hash=_sha256(pdf_data),
            size=len(pdf_data),
        )
        session.add(exam_upload)
        session.flush()

        gs = GradingSession(
            blueprint_id=blueprint_id,
            class_id=class_id,
            exam_type_id=exam_type_id,
            student_id=sid,
            exam_upload_id=exam_upload.id,
            batch_id=batch_id,
            queue_position=position,
        )
        session.add(gs)
        session.flush()

        created.append({
            "session_id": gs.id,
            "student_id": sid,
            "student_name": student_names[sid],
            "queue_position": position,
        })

    session.commit()

    return {
        "success": True,
        "batch_id": batch_id,
        "first_session_id": created[0]["session_id"],
        "sessions": created,
    }


@router.get("/sessions/{session_id}/stream")
async def stream_grading(
    session_id: str,
    force_restart: bool = Query(False),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    SSE stream for one student's grading.

    1. Fork blueprint checkpoint → student thread (idempotent SQL copy)
    2. Resume graph with student exam path → enters grade_agent phase
    3. Agent grades each question, emitting question_result custom events
    4. Graph suspends at grade_interrupt → event: interrupt {"breakdown":[...]}
    5. Teacher POSTs /review to approve/edit/cancel

    force_restart=true: clears results, deletes checkpoint, re-forks, re-runs.
    """
    teacher_id = int(teacher["id"])
    gs = _get_owned_grading_session_or_404(session, session_id, teacher_id)

    if gs.status not in ("pending",) and not force_restart:
        raise AppError(
            "GRADING_SESSION_NOT_PENDING",
            f"Session status is '{gs.status}'. Pass force_restart=true to re-run.",
            409,
        )

    if force_restart and gs.status != "pending":
        for r in session.exec(
            select(GradingQuestionResult).where(GradingQuestionResult.session_id == session_id)
        ).all():
            session.delete(r)
        try:
            from backend.agents.db import delete_thread
            await delete_thread(gs.thread_id)
        except Exception as exc:
            logger.warning("force_restart: delete checkpoint %s: %s", gs.thread_id, exc)
        gs.status = "pending"
        session.add(gs)
        session.commit()

    bp = session.get(GradingBlueprint, gs.blueprint_id)
    exam_upload = session.get(ExamUpload, gs.exam_upload_id)
    if bp is None or exam_upload is None:
        raise AppError("GRADING_DATA_MISSING", "Blueprint or exam upload not found.", 404)

    blueprint_thread_id = bp.analysis_thread_id
    student_thread_id = gs.thread_id
    student_exam_path = exam_upload.file_path

    gs.status = "reviewing"
    session.add(gs)
    session.commit()

    async def event_stream() -> AsyncIterator[str]:
        from backend.agents.grading_agent.agent import get_grading_graph
        from backend.agents.db import fork_thread
        from langgraph.types import Command

        try:
            await fork_thread(blueprint_thread_id, student_thread_id)

            graph = await get_grading_graph()
            config = {"configurable": {"thread_id": student_thread_id}}
            resume_cmd = Command(resume={"student_exam_path": student_exam_path})

            async for sse_frame in _stream_graph(graph, resume_cmd, config):
                yield sse_frame

            yield _sse("done", "")

        except Exception as exc:
            logger.exception("Grading stream error session=%s", session_id)
            yield _sse("error", str(exc))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/review")
async def review_session(
    session_id: str,
    body: ReviewRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Teacher submits review after the interrupt event.

    action=approve : saves GradingQuestionResult rows, normalises to 0-20, calls save_grade().
    action=cancel  : skips this student (no grade saved), marks session cancelled.

    Both return next_session_id (next pending in same batch) or null (batch complete).
    """
    teacher_id = int(teacher["id"])
    gs = _get_owned_grading_session_or_404(session, session_id, teacher_id)

    if gs.status != "reviewing":
        raise AppError(
            "GRADING_SESSION_NOT_REVIEWING",
            f"Session status is '{gs.status}', expected 'reviewing'.",
            409,
        )

    # Find next pending session before mutating current one
    next_session = session.exec(
        select(GradingSession).where(
            GradingSession.batch_id == gs.batch_id,
            GradingSession.status == "pending",
            GradingSession.queue_position > gs.queue_position,
        ).order_by(GradingSession.queue_position)
    ).first()
    next_session_id: Optional[str] = next_session.id if next_session else None

    # ── Cancel ────────────────────────────────────────────────────────────
    if body.action == "cancel":
        gs.status = "cancelled"
        session.add(gs)
        session.commit()
        return {
            "success": True,
            "action": "cancelled",
            "session_id": session_id,
            "next_session_id": next_session_id,
        }

    # ── Approve ───────────────────────────────────────────────────────────
    from backend.agents.grading_agent.agent import get_grading_graph
    from langgraph.types import Command

    graph = await get_grading_graph()
    config = {"configurable": {"thread_id": gs.thread_id}}

    await graph.ainvoke(
        Command(resume={"decisions": [d.model_dump() for d in body.decisions],
                        "action": body.action}),
        config=config,
    )

    final_state = await graph.aget_state(config)
    breakdown: List[dict] = final_state.values.get("breakdown", [])
    decision_map: Dict[int, float] = {d.question_number: d.awarded_points for d in body.decisions}

    # Clear previous results (idempotent on retry)
    for r in session.exec(
        select(GradingQuestionResult).where(GradingQuestionResult.session_id == session_id)
    ).all():
        session.delete(r)

    total_awarded = 0.0
    total_max = 0.0
    for q in breakdown:
        qnum = q.get("question_number", 0)
        agent_awarded = float(q.get("awarded_points", 0))
        max_pts = float(q.get("max_points", 0))
        teacher_pts = decision_map.get(qnum)
        final_pts = teacher_pts if teacher_pts is not None else agent_awarded
        is_override = teacher_pts is not None and teacher_pts != agent_awarded

        session.add(GradingQuestionResult(
            session_id=session_id,
            question_number=qnum,
            question_label=q.get("label", f"Q{qnum}"),
            max_points=max_pts,
            awarded_points=final_pts,
            reasoning=q.get("reasoning", ""),
            teacher_override=is_override,
        ))
        total_awarded += final_pts
        total_max += max_pts

    normalised = round((total_awarded / total_max) * 20, 2) if total_max > 0 else 0.0
    normalised = max(0.0, min(20.0, normalised))

    from backend.grades.main import save_grade
    grade_result = save_grade(
        session,
        {"id": str(teacher_id)},
        class_id=gs.class_id,
        student_id=gs.student_id,
        exam_type_id=gs.exam_type_id,
        value=normalised,
    )

    gs.status = "approved"
    session.add(gs)
    session.commit()

    return {
        "success": True,
        "action": "approved",
        "session_id": session_id,
        "total_awarded": total_awarded,
        "total_max": total_max,
        "normalised_grade": normalised,
        "grade": grade_result.get("grade"),
        "next_session_id": next_session_id,
    }


@router.get("/sessions")
def list_sessions(
    blueprint_id: Optional[int] = Query(None),
    batch_id: Optional[str] = Query(None),
    class_id: Optional[int] = Query(None),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """List grading sessions. Filterable by blueprint_id, batch_id, or class_id."""
    teacher_id = int(teacher["id"])

    query = (
        select(GradingSession)
        .join(GradingBlueprint, GradingBlueprint.id == GradingSession.blueprint_id)
        .where(GradingBlueprint.teacher_id == teacher_id)
    )

    if blueprint_id is not None:
        _get_owned_blueprint_or_404(session, blueprint_id, teacher_id, allow_deleted=True)
        query = query.where(GradingSession.blueprint_id == blueprint_id)
    if batch_id is not None:
        query = query.where(GradingSession.batch_id == batch_id)
    if class_id is not None:
        get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)
        query = query.where(GradingSession.class_id == class_id)

    rows = session.exec(query.order_by(GradingSession.queue_position)).all()
    return {"success": True, "sessions": [_serialize_grading_session(r) for r in rows]}


# ─── Serialisers ──────────────────────────────────────────────────────────────

def _serialize_exam_paper(r: ExamPaper) -> Dict[str, Any]:
    return {
        "id": r.id,
        "class_id": r.class_id,
        "filename": r.filename,
        "size": r.size,
        "created_at": r.created_at,
    }


def _serialize_blueprint(r: GradingBlueprint) -> Dict[str, Any]:
    return {
        "id": r.id,
        "title": r.title,
        "exam_paper_id": r.exam_paper_id,
        "lesson_doc_ids": json.loads(r.lesson_doc_ids),
        "preferences": r.preferences,
        "style_guide": r.style_guide,
        "deleted": r.deleted,
        "created_at": r.created_at,
    }


def _serialize_grading_session(r: GradingSession) -> Dict[str, Any]:
    return {
        "id": r.id,
        "blueprint_id": r.blueprint_id,
        "class_id": r.class_id,
        "exam_type_id": r.exam_type_id,
        "student_id": r.student_id,
        "batch_id": r.batch_id,
        "queue_position": r.queue_position,
        "status": r.status,
        "created_at": r.created_at,
    }


# ─── Access helpers ───────────────────────────────────────────────────────────

def _get_owned_exam_paper_or_404(session: Session, paper_id: int, teacher_id: int) -> ExamPaper:
    paper = session.get(ExamPaper, paper_id)
    if paper is None:
        raise AppError("GRADING_PAPER_NOT_FOUND", "Exam paper not found.", 404)
    if paper.teacher_id != teacher_id:
        raise AppError("GRADING_PAPER_FORBIDDEN", "Access denied.", 403)
    return paper  # type: ignore[return-value]


def _get_owned_blueprint_or_404(
    session: Session, blueprint_id: int, teacher_id: int, allow_deleted: bool = False
) -> GradingBlueprint:
    bp = session.get(GradingBlueprint, blueprint_id)
    if bp is None:
        raise AppError("GRADING_BLUEPRINT_NOT_FOUND", "Blueprint not found.", 404)
    if bp.teacher_id != teacher_id:
        raise AppError("GRADING_BLUEPRINT_FORBIDDEN", "Access denied.", 403)
    if bp.deleted and not allow_deleted:
        raise AppError("GRADING_BLUEPRINT_DELETED", "Blueprint has been deleted.", 404)
    return bp  # type: ignore[return-value]


def _get_owned_grading_session_or_404(
    session: Session, session_id: str, teacher_id: int
) -> GradingSession:
    gs = session.get(GradingSession, session_id)
    if gs is None:
        raise AppError("GRADING_SESSION_NOT_FOUND", "Grading session not found.", 404)
    bp = session.get(GradingBlueprint, gs.blueprint_id)
    if bp is None or bp.teacher_id != teacher_id:
        raise AppError("GRADING_SESSION_FORBIDDEN", "Access denied.", 403)
    return gs  # type: ignore[return-value]
