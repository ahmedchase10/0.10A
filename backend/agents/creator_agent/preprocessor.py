"""
backend/agents/creator_agent/preprocessor.py
---------------------------------------------
Background task: extract a structured JSON overview from a lesson PDF.

Pipeline per document:
  1. PyMuPDF (fitz) extracts text from each page
  2. Pages with < 100 chars of text → Tesseract OCR fallback (CPU, no GPU)
  3. Concatenated text sent to local Ollama (Qwen small model)
  4. Ollama returns structured JSON: {sections: [{title, subsections: [{title, topics: [str]}]}]}
  5. Overview written to Upload.overview in Postgres

Triggered automatically after embed_upload_task succeeds (same background thread).
On failure: Upload.overview stays null — frontend retries via POST /agents/creator/retry-overview.
"""
import json
import logging
import re

import requests

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# ── Tesseract availability flag ───────────────────────────────────────────────
_TESSERACT_AVAILABLE: bool | None = None


def _check_tesseract() -> bool:
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
    except Exception:
        _TESSERACT_AVAILABLE = False
        logger.warning("Tesseract not available — OCR fallback disabled.")
    return _TESSERACT_AVAILABLE


_MIN_TEXT_CHARS = 100

_OVERVIEW_SYSTEM = (
    "You are a document structure extractor.\n"
    "Given the text of a PDF document, output ONLY a valid JSON object with this exact shape:\n"
    '{"sections": [{"title": "...", "subsections": [{"title": "...", "topics": ["...", "..."]}]}]}\n\n'
    "Rules:\n"
    "- Output ONLY the JSON. No explanation, no markdown fences, no preamble.\n"
    "- sections = top-level chapters or major parts of the document.\n"
    "- subsections = sub-chapters or named sections within each chapter.\n"
    "- topics = specific concepts, techniques, or subjects discussed (short phrases, 2-8 words each).\n"
    "- If the document has no clear sections, use a single section titled after the document's main subject.\n"
    "- Do NOT fabricate content — only describe what is actually present in the text.\n"
    "- Keep titles concise (max 80 chars)."
)


def _extract_text_from_pdf(file_path: str) -> str:
    """Extract text per page; Tesseract OCR fallback for image-heavy pages."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("pymupdf is required: pip install pymupdf") from exc

    tesseract_ok = _check_tesseract()
    parts: list[str] = []

    doc = fitz.open(file_path)
    try:
        for page_num, page in enumerate(doc):
            text = page.get_text("text").strip()

            if len(text) < _MIN_TEXT_CHARS and tesseract_ok:
                try:
                    import io
                    import pytesseract
                    from PIL import Image

                    mat = fitz.Matrix(1.5, 1.5)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img, lang="fra+eng", config="--psm 3").strip()
                    if len(ocr_text) > len(text):
                        text = ocr_text
                except Exception as ocr_exc:
                    logger.warning("OCR failed on page %d: %s", page_num + 1, ocr_exc)

            if text:
                parts.append(f"=== Page {page_num + 1} ===\n{text}")
    finally:
        doc.close()

    return "\n\n".join(parts)


def _call_ollama_for_overview(full_text: str) -> dict:
    """Call local Ollama to produce the structured JSON overview."""
    trimmed = full_text[:12_000] if len(full_text) > 12_000 else full_text

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _OVERVIEW_SYSTEM},
            {"role": "user", "content": trimmed},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.1, "top_p": 0.9, "num_predict": 2048},
    }

    resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
    resp.raise_for_status()
    raw: str = resp.json()["message"]["content"].strip()

    # Strip accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE).strip()

    overview = json.loads(raw)

    if "sections" not in overview or not isinstance(overview["sections"], list):
        raise ValueError(f"Ollama response missing 'sections' key: {raw[:200]}")

    return overview


def generate_overview_task(file_path: str, upload_id: str, db_url: str) -> None:
    """
    Background task: generate and store a structured doc overview for an Upload.

    Mirrors embed_upload_task signature — called from the same background thread
    in backend/lessons/main.py after embedding completes.

    Args:
        file_path:  Absolute path to the PDF on disk.
        upload_id:  Primary key of the Upload row (str UUID).
        db_url:     SQLAlchemy connection string.
    """
    logger.info("Overview generation started for upload %s", upload_id)

    from sqlmodel import Session as SyncSession, create_engine
    from backend.server.db.dbModels import Upload

    engine = create_engine(db_url, echo=False)
    try:
        try:
            full_text = _extract_text_from_pdf(file_path)
        except Exception as exc:
            logger.error("Overview: PDF text extraction failed for %s: %s", upload_id, exc)
            return

        if not full_text.strip():
            logger.warning("Overview: no text extracted from %s — skipping", upload_id)
            return

        try:
            overview = _call_ollama_for_overview(full_text)
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Overview: Ollama not reachable for upload %s — will remain null (retry available)",
                upload_id,
            )
            return
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Overview: Ollama returned invalid JSON for %s: %s", upload_id, exc)
            return
        except Exception as exc:
            logger.error("Overview: Ollama call failed for %s: %s", upload_id, exc)
            return

        with SyncSession(engine) as session:
            upload = session.get(Upload, upload_id)
            if upload:
                upload.overview = overview
                session.add(upload)
                session.commit()
                logger.info(
                    "Overview stored for upload %s (%d sections)",
                    upload_id, len(overview.get("sections", [])),
                )
            else:
                logger.warning("Overview: Upload %s not found in DB", upload_id)

    except Exception as exc:
        logger.error("Overview: unexpected error for upload %s: %s", upload_id, exc)
    finally:
        engine.dispose()

