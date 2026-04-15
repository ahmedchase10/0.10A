from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlmodel import Session

from backend.lessons.main import list_lesson_uploads, upload_lesson_file, delete_lesson_upload
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("")
def list_lessons_route(
    class_id: int = Query(...),
    limit: int = Query(20),
    offset: int = Query(0),
    sort: str = Query("created_at_desc"),
    refresh: bool = Query(True),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return list_lesson_uploads(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        limit=limit,
        offset=offset,
        sort=sort,
        refresh=refresh,
    )


@router.post("/upload")
def upload_lesson_route(
    file: UploadFile = File(...),
    class_id: int = Form(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return upload_lesson_file(
        session=session,
        teacher_payload=teacher,
        upload_file=file,
        class_id=class_id,
    )


@router.delete("/{upload_id}")
def delete_lesson_route(
    upload_id: str,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return delete_lesson_upload(
        session=session,
        teacher_payload=teacher,
        upload_id=upload_id
    )