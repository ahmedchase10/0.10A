"""
backend/agents/grading_agent/tools.py
--------------------------------------
Tools available to the grading agent:

  read_pdf_as_images  — render every page of a local PDF to a scaled base64 JPEG
  rag_retrieve        — re-exported from pedagogical_agent.tools (no duplication)
"""
import base64
import logging
from typing import List

from langchain_core.tools import tool

# Re-export RAG tool — identical implementation, shared code
from backend.agents.pedagogical_agent.tools import rag_retrieve  # noqa: F401

logger = logging.getLogger(__name__)


@tool
def read_pdf_as_images(file_path: str, max_px: int = 1024) -> List[dict]:
    """
    Render every page of a PDF file to a base64-encoded JPEG image.

    Use this tool to read:
      - The exam question paper (to understand what is being asked)
      - The teacher-provided correction PDF (to understand the expected answers)
      - A student's exam paper (to read and grade their answers)

    Args:
        file_path: Absolute path to the PDF on disk.
        max_px:    Maximum pixel size for the longest page dimension.
                   Choose based on content complexity:
                     512  → plain short-answer text
                     768  → dense text, tables, formulas
                     1280 → diagrams, graphs, figures
                     1536 → highly detailed technical visuals

    Returns:
        List of {"page_number": int (0-based), "image_b64": str (JPEG base64)}
    """
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise RuntimeError("pymupdf is required: pip install pymupdf") from exc

    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        raise RuntimeError(f"Cannot open PDF at '{file_path}': {exc}") from exc

    pages = []
    try:
        for i, page in enumerate(doc):
            rect = page.rect
            longest = max(rect.width, rect.height)
            zoom = min(max_px / longest, 2.0) if longest > 0 else 1.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("jpeg")
            pages.append({
                "page_number": i,
                "image_b64": base64.b64encode(img_bytes).decode(),
            })
            logger.debug("read_pdf_as_images: page %d rendered (%dx%d px)", i, pix.width, pix.height)
    finally:
        doc.close()

    logger.info("read_pdf_as_images: %s → %d pages at max_px=%d", file_path, len(pages), max_px)
    return pages

