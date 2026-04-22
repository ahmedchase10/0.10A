import os
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from sqlmodel import Session

from backend.lessons.main import (
    delete_lesson_upload,
    embed_upload_task,
    list_lesson_uploads,
    retry_embed_uploads,
    upload_lesson_file,
    UPLOADS_ROOT,
)
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session, DATABASE_URL

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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    class_id: int = Form(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    result = upload_lesson_file(
        session=session,
        teacher_payload=teacher,
        upload_file=file,
        class_id=class_id,
    )

    # Queue embedding unless the file was a duplicate (already embedded)
    upload_info = result.get("upload", {})
    if not upload_info.get("already_exists", True):
        upload_id = upload_info["id"]
        from pathlib import Path

        absolute_path = str(
            UPLOADS_ROOT.parent
            / Path("uploads")
            / "classes"
            / str(class_id)
            / upload_info["name"]
        )
        background_tasks.add_task(
            embed_upload_task,
            file_path=absolute_path,
            doc_id=upload_id,
            upload_id=upload_id,
            db_url=DATABASE_URL,
        )

    return result


@router.delete("/{upload_id}")
def delete_lesson_route(
    upload_id: str,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return delete_lesson_upload(
        session=session,
        teacher_payload=teacher,
        upload_id=upload_id,
    )


@router.post("/retry-embed")
def retry_embed_route(
    background_tasks: BackgroundTasks,
    class_id: int = Query(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    result = retry_embed_uploads(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        db_url=DATABASE_URL,
    )

    # Queue each unembedded upload
    from pathlib import Path
    from sqlmodel import select
    from backend.server.db.dbModels import Upload

    for upload_id in result["queued"]:
        upload = session.get(Upload, upload_id)
        if upload:
            absolute_path = str(UPLOADS_ROOT.parent / upload.file_path)
            background_tasks.add_task(
                embed_upload_task,
                file_path=absolute_path,
                doc_id=upload_id,
                upload_id=upload_id,
                db_url=DATABASE_URL,
            )

    return result
