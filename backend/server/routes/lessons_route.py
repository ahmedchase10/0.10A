from typing import Any, Dict , Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from sqlmodel import Session
from pathlib import Path
from backend.lessons.main import (
    delete_lesson_upload,
    embed_upload_task,
    list_lesson_uploads,
    retry_embed_uploads,
    upload_lesson_file,
    UPLOADS_ROOT,
    assign_global_upload_to_class,
)
from backend.server.auth.dependencies import require_auth
from backend.server.db import GlobalUpload
from backend.server.db.engine import get_session, DATABASE_URL

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("")
def list_lessons_route(
    class_id:Optional[int] =  Query(None),
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
        class_id=class_id,  # Passes None if not provided
        limit=limit,
        offset=offset,
        sort=sort,
        refresh=refresh,
    )

@router.post("/upload")
def upload_lesson_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    result = upload_lesson_file(
        session=session,
        upload_file=file,
        teacher_id=teacher["id"],
    )

    upload_info = result.get("upload", {})
    if not upload_info.get("already_exists", True):
        upload_id = upload_info["id"]
        absolute_path = str(
            UPLOADS_ROOT.parent
            / Path("uploads")
            /"teachers"
            / str(teacher["id"])
            / upload_info["name"]
        )
        background_tasks.add_task(
            embed_upload_task,
            file_path=absolute_path,
            doc_id=upload_id,
            upload_id=upload_id,
            db_url=DATABASE_URL,
            session=session,
        )

    return result

@router.post("/assign")
def assign_global_upload_route(
    global_upload_id: str = Query(...),
    class_id: int = Query(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return assign_global_upload_to_class(
        session=session,
        teacher_payload=teacher,
        global_upload_id=global_upload_id,
        class_id=class_id,
    )
from typing import Optional  # 🔥 Add if not already imported

@router.delete("/{upload_id}")
def delete_lesson_route(
    upload_id: str,
    class_id: Optional[int] = Query(None),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return delete_lesson_upload(
        session=session,
        teacher_payload=teacher,
        upload_id=upload_id,
        class_id=class_id,
    )

@router.post("/retry-embed")
def retry_embed_route(
    background_tasks: BackgroundTasks,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    result = retry_embed_uploads(
        session=session,
        teacher_payload=teacher,
    )
    from backend.server.db import GlobalUpload

    for upload_id in result["queued"]:
        global_upload = session.get(GlobalUpload, upload_id)
        if global_upload and (not global_upload.embedded or global_upload.overview is None):
            absolute_path = str(UPLOADS_ROOT/ global_upload.file_path)
            background_tasks.add_task(
                embed_upload_task,
                file_path=absolute_path,
                doc_id=upload_id,
                upload_id=upload_id,
                db_url=DATABASE_URL,
                session=session,
            )

    return result