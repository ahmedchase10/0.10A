import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from fastapi import UploadFile
from sqlalchemy import asc, desc
from sqlmodel import Session, select

from backend.classes.access import get_owned_class_or_403
from backend.models import AppError
from backend.server.db.dbModels import Upload

logger = logging.getLogger(__name__)

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
            "embedded": row.embedded,
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
            "embed_queued": True,
            "upload": {
                "id": record.id,
                "name": record.filename,
                "size": record.size,
                "embedded": record.embedded,
                "created_at": record.created_at,
                "already_exists": False,
            },
        }
    finally:
        upload_file.file.close()
        if temp_path.exists():
            temp_path.unlink()


def embed_upload_task(file_path: str, doc_id: str, upload_id: str, db_url: str) -> None:
    """
    Background task: embed a PDF into Weaviate and mark Upload.embedded = True.
    Runs in a thread pool (FastAPI BackgroundTasks).
    Uses its own DB session and RAG instances so it's isolated from the request.
    """
    import sqlalchemy
    from sqlmodel import Session as SyncSession, create_engine
    from backend.rag.document_processor import DocumentProcessor
    from backend.rag.vector_store import VectorStore

    engine = create_engine(db_url, echo=False)

    processor = DocumentProcessor()
    store = VectorStore()
    try:
        document, pages = processor.process_pdf(file_path, source="lesson", doc_id=doc_id)
        store.store_pages_batch(pages, document)

        with SyncSession(engine) as session:
            upload = session.get(Upload, upload_id)
            if upload:
                upload.embedded = True
                session.add(upload)
                session.commit()
        logger.info("Embedded doc %s (%s)", doc_id, upload_id)
    except Exception as exc:
        logger.error("Embedding failed for upload %s: %s", upload_id, exc)
        # embedded stays False — frontend shows warning
    finally:
        processor.close()
        store.close()
        engine.dispose()


def delete_lesson_upload(
    session: Session,
    teacher_payload: Dict[str, Any],
    upload_id: str,
) -> Dict[str, Any]:
    from backend.rag.vector_store import VectorStore
    from backend.config import PAGES_STORAGE_PATH

    teacher_id = int(teacher_payload["id"])

    upload = session.exec(select(Upload).where(Upload.id == upload_id)).first()
    if upload is None:
        raise AppError("LESSONS_UPLOAD_NOT_FOUND", "Upload not found.", 404)

    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=upload.class_id)

    # ── Delete PDF from disk ───────────────────────────────────────────────
    absolute_path = UPLOADS_ROOT.parent / upload.file_path
    file_deleted = False
    try:
        if absolute_path.exists():
            absolute_path.unlink()
            file_deleted = True
    except OSError:
        raise AppError("LESSONS_DELETE_FILE_FAILED", "Failed to delete file from disk.", 500)

    # ── Delete page images from disk ──────────────────────────────────────
    pages_dir = Path(PAGES_STORAGE_PATH)
    for page_img in pages_dir.glob(f"{upload_id}_page_*.png"):
        try:
            page_img.unlink()
        except OSError:
            logger.warning("Could not delete page image %s", page_img)

    # ── Delete vectors from Weaviate ──────────────────────────────────────
    if upload.embedded:
        try:
            store = VectorStore()
            store.delete_by_doc_id(upload_id)
            store.close()
        except Exception as exc:
            logger.warning("Weaviate cleanup failed for %s: %s", upload_id, exc)

    session.delete(upload)
    session.commit()

    return {
        "success": True,
        "deleted": {
            "id": upload_id,
            "name": upload.filename,
            "file_deleted": file_deleted,
        },
    }


def retry_embed_uploads(
    session: Session,
    teacher_payload: Dict[str, Any],
    class_id: int,
    db_url: str,
) -> Dict[str, Any]:
    """Queue background embedding for all unembedded uploads in a class."""
    teacher_id = int(teacher_payload["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    unembedded = session.exec(
        select(Upload).where(
            Upload.class_id == class_id,
            Upload.embedded == False,  # noqa: E712
        )
    ).all()

    queued: List[str] = []
    for upload in unembedded:
        absolute_path = str(UPLOADS_ROOT.parent / upload.file_path)
        if Path(absolute_path).exists():
            queued.append(upload.id)
        else:
            logger.warning("File missing for upload %s, skipping retry", upload.id)

    return {"success": True, "queued": queued}

