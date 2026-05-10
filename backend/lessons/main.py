import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List ,Optional

from fastapi import UploadFile
from sqlalchemy import asc, desc, or_
from sqlmodel import Session, select

from backend.classes.access import get_owned_class_or_403
from backend.models import AppError
from backend.server.db.dbModels import Upload,GlobalUpload,ProcessingJob

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


def _next_available_filename_teacher(session: Session, teacher_id: int, preferred_name: str, teacher_dir: Path) -> str:
    base, ext = os.path.splitext(preferred_name)
    candidate = preferred_name
    counter = 1
    while True:
        in_db = session.exec(
            select(GlobalUpload).where(
                GlobalUpload.teacher_id == teacher_id,
                GlobalUpload.filename == candidate,
            )
        ).first()
        on_disk = (teacher_dir / candidate).exists()
        if in_db is None and not on_disk:
            return candidate
        candidate = f"{base} ({counter}){ext}"
        counter += 1

def _resolve_sort(sort: str):
    sort_map = {
        "created_at_desc": desc(GlobalUpload.created_at),
        "created_at_asc": asc(GlobalUpload.created_at),
        "name_asc": asc(GlobalUpload.filename),
        "name_desc": desc(GlobalUpload.filename),
        "size_asc": asc(GlobalUpload.size),
        "size_desc": desc(GlobalUpload.size),
    }
    order_clause = sort_map.get(sort)
    if order_clause is None:
        raise AppError("LESSONS_INVALID_SORT", "Invalid sort value.", 400)
    return order_clause

def _cleanup_missing_uploads(session: Session, teacher_id: int, class_id: Optional[int] = None) -> int:
    if class_id is not None:
        rows = session.exec(
            select(GlobalUpload)
            .join(Upload, GlobalUpload.file_hash == Upload.file_hash)
            .where(Upload.class_id == class_id)
        ).all()
    else:
        rows = session.exec(
            select(GlobalUpload).where(GlobalUpload.teacher_id == teacher_id)
        ).all()

    removed = 0
    for row in rows:
        rel_path = row.file_path

        if rel_path.startswith("uploads/"):
            rel_path = rel_path[len("uploads/"):]
        absolute_path = (UPLOADS_ROOT / rel_path).resolve()

        if not absolute_path.exists():
            session.delete(row)
            removed += 1

    if removed > 0:
        session.commit()
    return removed


from typing import Any, Dict, List, Optional   # 🔥 Add Optional

from typing import Any, Dict, List, Optional  # 🔥 Ensure Optional is imported


def list_lesson_uploads(
        session: Session,
        teacher_payload: Dict[str, Any],
        *,
        class_id: Optional[int],
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
    order_clause = _resolve_sort(sort)

    # 🔹 Build base query
    if class_id is not None:
        get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)
        if refresh:
            _cleanup_missing_uploads(session, teacher_id,class_id=class_id)

        query = (
            select(GlobalUpload)
            .join(Upload, GlobalUpload.file_hash == Upload.file_hash)
            .where(Upload.class_id == class_id)
        )
    else:
        # 🔹 Global library view
        if refresh:
            _cleanup_missing_uploads(session, teacher_id, class_id=None)
        query = select(GlobalUpload)

    # 🔹 Execute with pagination & sorting
    rows = session.exec(
        query
        .order_by(order_clause, asc(GlobalUpload.id))
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
                "overview_ready": row.overview is not None,
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
    upload_file: UploadFile,
    teacher_id: int,
) -> Dict[str, Any]:
    if not upload_file.filename:
        raise AppError("LESSONS_MISSING_FILENAME", "Uploaded file must have a filename.", 400)

    sanitized_name = _sanitize_filename(upload_file.filename)
    teacher_dir = UPLOADS_ROOT / "teachers" / str(teacher_id)
    teacher_dir.mkdir(parents=True, exist_ok=True)

    temp_path = teacher_dir / f".tmp_{os.urandom(8).hex()}"
    hasher = hashlib.sha256()
    total_size = 0

    try:
        with temp_path.open("wb") as temp_file:
            while chunk := upload_file.file.read(CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    raise AppError("LESSONS_FILE_TOO_LARGE", "File exceeds 150MB limit.", 413)
                hasher.update(chunk)
                temp_file.write(chunk)

        file_hash = hasher.hexdigest()

        existing_global = session.exec(
            select(GlobalUpload).where(GlobalUpload.file_hash == file_hash)
        ).first()

        if existing_global:
            temp_path.unlink()
            return {
                "success": True,
                "upload": {
                    "id": existing_global.id,
                    "name": existing_global.filename,
                    "size": existing_global.size,
                    "embedded": existing_global.embedded,
                    "overviewed":existing_global.overview is not None,
                    "created_at": existing_global.created_at,
                    "already_exists": True,
                },
            }

        final_name = _next_available_filename_global(session, sanitized_name, teacher_dir)
        final_path = teacher_dir / final_name
        os.replace(str(temp_path), str(final_path))
        relative_path = str(Path() / "teachers" / str(teacher_id) / final_name)
        global_upload = GlobalUpload(
            teacher_id=teacher_id,
            filename=final_name,
            file_path=relative_path,
            file_hash=file_hash,
            size=total_size,
        )
        session.add(global_upload)
        session.commit()
        session.refresh(global_upload)

        return {
            "success": True,
            "embed_queued": True,
            "overview_queued":True,
            "upload": {
                "id": global_upload.id,
                "name": global_upload.filename,
                "size": global_upload.size,
                "overviewed":global_upload.overview is not None,
                "embedded": global_upload.embedded,
                "created_at": global_upload.created_at,
                "already_exists": False,
            },
        }
    finally:
        upload_file.file.close()
        if temp_path.exists():
            temp_path.unlink()


def _next_available_filename_global(session: Session, preferred_name: str, global_dir: Path) -> str:
    base, ext = os.path.splitext(preferred_name)
    candidate = preferred_name
    counter = 1
    while True:
        in_db = session.exec(
            select(GlobalUpload).where(GlobalUpload.filename == candidate)
        ).first()
        on_disk = (global_dir / candidate).exists()
        if in_db is None and not on_disk:
            return candidate
        candidate = f"{base} ({counter}){ext}"
        counter += 1

def assign_global_upload_to_class(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    global_upload_id: str,
    class_id: int,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    global_upload = session.get(GlobalUpload, global_upload_id)
    if not global_upload:
        raise AppError("LESSONS_UPLOAD_NOT_FOUND", "Global upload not found.", 404)

    existing_link = session.exec(
        select(Upload).where(
            Upload.class_id == class_id,
            Upload.file_hash == global_upload.file_hash,
        )
    ).first()

    if existing_link:
        return {
            "success": True,
            "upload": {
                "id": global_upload.id,
                "name": global_upload.filename,
                "size": global_upload.size,
                "embedded": global_upload.embedded,
                "overviewed": global_upload.overview is not None,
                "created_at": global_upload.created_at,
                "already_exists": True,
            },
        }

    new_link = Upload(
        class_id=class_id,
        file_hash=global_upload.file_hash,
    )
    session.add(new_link)
    session.commit()

    return {
        "success": True,
        "upload": {
            "id": global_upload.id,
            "name": global_upload.filename,
            "size": global_upload.size,
            "embedded": global_upload.embedded,
            "overviewed": global_upload.overview is not None,
            "created_at": global_upload.created_at,
            "already_exists": False,
        },
    }

def embed_upload_task(file_path: str, doc_id: str, upload_id: str, db_url: str, session:Session) -> None:
    from backend.rag.document_processor import DocumentProcessor
    from backend.rag.vector_store import VectorStore

    upload = session.get(GlobalUpload, upload_id)
    if not upload:
        logger.warning("GlobalUpload %s not found", upload_id)
        return
    job = session.exec(select(ProcessingJob).where(ProcessingJob.file_hash == upload.file_hash).with_for_update()).first()
    if job is None:
        job = ProcessingJob(file_hash=upload.file_hash)
        session.add(job)
        session.flush()
    processor = None
    store = VectorStore()
    if job.embedding_in_progress:
        logger.info(" Skip: Embedding for doc %s is already in progress.", doc_id)
        store.close()
    elif store.doc_already_embedded(doc_id):
        logger.info(" Skip: Doc %s is already embedded.", doc_id)
        store.close()
        if upload and not upload.embedded:
            upload.embedded = True
            session.commit()
    else:
        try:
            processor = DocumentProcessor()
            document, pages = processor.process_pdf(file_path, source="lesson", doc_id=doc_id)
            store.store_pages_batch(pages, document)
            job.embedding_in_progress = True
            session.commit()
            if upload:
                upload.embedded = True
                session.add(upload)
                session.commit()
                logger.info("Embedded doc %s (%s)", doc_id, upload_id)
        except Exception as exc:
            logger.error("Embedding failed for upload %s: %s", upload_id, exc)
            job.embedding_in_progress=False
            session.commit()
        finally:
            if processor:
                processor.close()
            if store:
                store.close()
            job.embedding_in_progress = False
            session.add(job)
            session.commit()

    if job.overview_in_progress:
        logger.info(" Skip: Overview for doc %s is already in progress.", doc_id)
    elif upload.overview is not None:
        logger.info(" Skip: Doc %s already has an overview.", doc_id)
    else:
        try:
            job.overview_in_progress = True
            session.add(job)
            session.commit()
            from backend.agents.creator_agent.preprocessor import generate_overview_task
            generate_overview_task(file_path, upload_id, db_url)
        except Exception as exc:
            logger.error("Overview task failed for upload %s: %s", upload_id, exc)
        finally:
            job.overview_in_progress = False
            session.add(job)
            session.commit()
    if not job.embedding_in_progress and not job.overview_in_progress:
        session.delete(job)
        session.commit()



def delete_lesson_upload(
    session: Session,
    teacher_payload: Dict[str, Any],
    upload_id: str,
    class_id: Optional[int] = None,
) -> Dict[str, Any]:
    from backend.rag.vector_store import VectorStore
    from backend.config import PAGES_STORAGE_PATH

    teacher_id = int(teacher_payload["id"])
    global_upload = session.get(GlobalUpload, upload_id)
    if not global_upload:
        raise AppError("LESSONS_UPLOAD_NOT_FOUND", "Upload not found.", 404)

    if global_upload.teacher_id != teacher_id:
        raise AppError("LESSONS_FORBIDDEN", "You do not own this upload.", 403)

    if class_id is not None:
        # 🔹 CLASS UNLINK: Only removes the linkage row
        get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)
        class_link = session.get(Upload, (class_id, global_upload.file_hash))
        if not class_link:
            raise AppError("LESSONS_UPLOAD_NOT_FOUND", "File not assigned to this class.", 404)

        session.delete(class_link)
        session.commit()
        return {
            "success": True,
            "deleted": {
                "id": upload_id,
                "name": global_upload.filename,
                "unlinked": True,
                "global_kept": True,
            },
        }


    absolute_path = UPLOADS_ROOT.parent / global_upload.file_path
    file_deleted = False
    try:
        if absolute_path.exists():
            absolute_path.unlink()
            file_deleted = True
    except OSError:
        logger.warning("Failed to delete file from disk: %s", absolute_path)

    pages_dir = Path(PAGES_STORAGE_PATH)
    for page_img in pages_dir.glob(f"{upload_id}_page_*.png"):
        try:
            page_img.unlink()
        except OSError:
            pass

    if global_upload.embedded:
        try:
            store = VectorStore()
            store.delete_by_doc_id(upload_id)
            store.close()
        except Exception as exc:
            logger.warning("Weaviate cleanup failed for %s: %s", upload_id, exc)

    session.delete(global_upload)
    session.commit()

    return {
        "success": True,
        "deleted": {
            "id": upload_id,
            "name": global_upload.filename,
            "file_deleted": file_deleted,
            "global_deleted": True,
        },
    }

def retry_embed_uploads(
    session: Session,
    teacher_payload: Dict[str, Any],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    all_uploads = session.exec(
        select(GlobalUpload).where(GlobalUpload.teacher_id == teacher_id)
    ).all()

    queued: List[str] = []
    for upload in all_uploads:
        needs_processing = (not upload.embedded) or (upload.overview is None)
        if not needs_processing:
            continue

        absolute_path = UPLOADS_ROOT / upload.file_path
        if not absolute_path.exists():
            logger.warning("File missing for upload %s, skipping", upload.id)
            continue

        queued.append(upload.id)

    return {"queued": queued, "total_queued": len(queued)}
