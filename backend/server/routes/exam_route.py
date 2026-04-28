import uuid
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlmodel import Session, select
from backend.models import AppError
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import (
    ExamPaper,
)
from backend.classes.access import get_owned_class_or_403
from backend.server.routes.grading_route import _get_owned_exam_paper_or_404, _serialize_exam_paper , _sha256

_BASE_DIR = Path(__file__).resolve().parents[3]
_EXAM_PAPERS_DIR  = _BASE_DIR / "uploads" / "exam_papers"
_EXAM_UPLOADS_DIR = _BASE_DIR / "uploads" / "exams"


def _exam_papers_dir(teacher_id: int) -> Path:
    p = _EXAM_PAPERS_DIR / str(teacher_id)
    p.mkdir(parents=True, exist_ok=True)
    return p



router = APIRouter(prefix="/exams", tags=["exam-papers"])
logger = logging.getLogger(__name__)

@router.post("/upload")
def upload_exam_paper(
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

    data = file.file.read()
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


@router.get("")
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


@router.delete("/delete/{paper_id}")
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
