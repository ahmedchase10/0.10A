import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict

from fastapi import UploadFile
from sqlmodel import Session, select

from backend.models import AppError
from backend.server.db.dbModels import Upload

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


def _next_available_filename(session: Session, teacher_id: int, preferred_name: str, teacher_dir: Path) -> str:
    base, ext = os.path.splitext(preferred_name)
    candidate = preferred_name
    counter = 1

    while True:
        in_db = session.exec(
            select(Upload).where(
                Upload.teacher_id == teacher_id,
                Upload.filename == candidate,
            )
        ).first()
        on_disk = (teacher_dir / candidate).exists()
        if in_db is None and not on_disk:
            return candidate
        candidate = f"{base} ({counter}){ext}"
        counter += 1


def upload_lesson_file(
    session: Session,
    teacher_payload: Dict[str, Any],
    upload_file: UploadFile,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if not upload_file.filename:
        raise AppError("LESSONS_MISSING_FILENAME", "Uploaded file must have a filename.", 400)

    sanitized_name = _sanitize_filename(upload_file.filename)
    teacher_dir = UPLOADS_ROOT / str(teacher_id)
    teacher_dir.mkdir(parents=True, exist_ok=True)

    temp_path = teacher_dir / f".tmp_{os.urandom(8).hex()}"

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
                Upload.teacher_id == teacher_id,
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

        final_name = _next_available_filename(session, teacher_id, sanitized_name, teacher_dir)
        final_path = teacher_dir / final_name
        os.replace(str(temp_path), str(final_path))

        relative_path = str(Path("uploads") / str(teacher_id) / final_name)
        record = Upload(
            teacher_id=teacher_id,
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

