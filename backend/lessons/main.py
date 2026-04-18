import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict

from fastapi import UploadFile
from sqlalchemy import asc, desc
from sqlmodel import Session, select

from backend.classes.access import get_owned_class_or_403
from backend.models import AppError
from backend.server.db.dbModels import Upload, Class

MAX_FILE_SIZE_BYTES = 150 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
UPLOADS_ROOT = Path(__file__).resolve().parents[2] / "uploads"


def _sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    safe_name = re.sub(r"[^A-Za-z0-9._()\- ]+", "_", safe_name)
    safe_name = re.sub(r"\s+", " ", safe_name).strip(" .")
    if not safe_name:
        safe_name = "file.pdf"

    base, ext = os.path.splitext(safe_name)
    ext = ext.lower()
    if ext != ".pdf":
        raise AppError("LESSONS_INVALID_FILE_TYPE", "Only PDF files are allowed.", 400)
    return f"{base}.pdf"


def _next_available_filename(session: Session, class_id: int, preferred_name: str, class_dir: Path) -> str:
    base, ext = os.path.splitext(preferred_name)
    candidate = preferred_name
    counter = 1

    while True:
        in_db = session.exec(
            select(Upload).where(
                Upload.class_id == class_id,
                Upload.filename == candidate,
            )
        ).first()
        on_disk = (class_dir / candidate).exists()
        if in_db is None and not on_disk:
            return candidate
        candidate = f"{base} ({counter}){ext}"
        counter += 1


def _resolve_sort(sort: str):
    sort_map = {
        "created_at_desc": desc(Upload.created_at),
        "created_at_asc": asc(Upload.created_at),
        "name_asc": asc(Upload.filename),
        "name_desc": desc(Upload.filename),
        "size_asc": asc(Upload.size),
        "size_desc": desc(Upload.size),
    }
    order_clause = sort_map.get(sort)
    if order_clause is None:
        raise AppError("LESSONS_INVALID_SORT", "Invalid sort value.", 400)
    return order_clause


def _cleanup_missing_uploads(session: Session, class_id: int) -> int:
    all_rows = session.exec(
        select(Upload).where(Upload.class_id == class_id)
    ).all()
    removed = 0

    for row in all_rows:
        absolute_path = UPLOADS_ROOT.parent / row.file_path
        if not absolute_path.exists():
            session.delete(row)
            removed += 1

    if removed:
        session.commit()
    return removed


def list_lesson_uploads(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    limit: int,
    offset: int,
    sort: str,
    refresh: bool,
) -> Dict[str, Any]:
    if limit < 1 or limit > 100:
        raise AppError("LESSONS_INVALID_PAGINATION", "Limit must be between 1 and 100.", 400)
    if offset < 0:
        raise AppError("LESSONS_INVALID_PAGINATION", "Offset must be 0 or greater.", 400)

    teacher_id = int(teacher_payload["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    if refresh:
        _cleanup_missing_uploads(session, class_id)

    order_clause = _resolve_sort(sort)
    rows = session.exec(
        select(Upload)
        .where(Upload.class_id == class_id)
        .order_by(order_clause, asc(Upload.id))
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "success": True,
        "uploads": [
            {
                "id": row.id,
                "name": row.filename,
                "size": row.size,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "sort": sort,
        },
    }


def upload_lesson_file(
    session: Session,
    teacher_payload: Dict[str, Any],
    upload_file: UploadFile,
    class_id: int,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    if not upload_file.filename:
        raise AppError("LESSONS_MISSING_FILENAME", "Uploaded file must have a filename.", 400)

    sanitized_name = _sanitize_filename(upload_file.filename)
    class_dir = UPLOADS_ROOT / "classes" / str(class_id)
    class_dir.mkdir(parents=True, exist_ok=True)

    temp_path = class_dir / f".tmp_{os.urandom(8).hex()}"

    hasher = hashlib.sha256()
    total_size = 0

    try:
        with temp_path.open("wb") as temp_file:
            while True:
                chunk = upload_file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    raise AppError(
                        "LESSONS_FILE_TOO_LARGE",
                        "File exceeds 150MB limit.",
                        413,
                    )
                hasher.update(chunk)
                temp_file.write(chunk)

        file_hash = hasher.hexdigest()

        existing = session.exec(
            select(Upload).where(
                Upload.class_id == class_id,
                Upload.file_hash == file_hash,
            )
        ).first()

        if existing:
            if temp_path.exists():
                temp_path.unlink()
            return {
                "success": True,
                "upload": {
                    "id": existing.id,
                    "name": existing.filename,
                    "size": existing.size,
                    "created_at": existing.created_at,
                    "already_exists": True,
                },
            }

        final_name = _next_available_filename(session, class_id, sanitized_name, class_dir)
        final_path = class_dir / final_name
        os.replace(str(temp_path), str(final_path))

        relative_path = str(Path("uploads") / "classes" / str(class_id) / final_name)
        record = Upload(
            class_id=class_id,
            filename=final_name,
            file_path=relative_path,
            file_hash=file_hash,
            size=total_size,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        return {
            "success": True,
            "upload": {
                "id": record.id,
                "name": record.filename,
                "size": record.size,
                "created_at": record.created_at,
                "already_exists": False,
            },
        }
    finally:
        upload_file.file.close()
        if temp_path.exists():
            temp_path.unlink()


def delete_lesson_upload(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    upload_id: str
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])
    
    upload = session.exec(
        select(Upload).where(Upload.id == upload_id)
    ).first()
    
    if not upload:
        raise AppError("LESSONS_NOT_FOUND", "Upload not found.", 404)
    
    # Verify teacher owns the class


    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=upload.class_id)
    
    # Delete file from disk
    file_path = Path(upload.file_path)
    absolute_path = UPLOADS_ROOT.parent / file_path
    if absolute_path.exists():
        absolute_path.unlink()
    
    # Delete from database
    session.delete(upload)
    session.commit()
    
    return {"success": True, "message": "Upload deleted successfully."}