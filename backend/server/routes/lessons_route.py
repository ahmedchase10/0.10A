from typing import Any, Dict

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

from backend.lessons.main import upload_lesson_file
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/upload")
def upload_lesson_route(
    file: UploadFile = File(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return upload_lesson_file(
        session=session,
        teacher_payload=teacher,
        upload_file=file,
    )

