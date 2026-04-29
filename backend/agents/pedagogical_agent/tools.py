"""
RAG tool + query rewriter for the pedagogical agent.
"""
import base64
import logging
from io import BytesIO
from typing import List

import requests
from langchain_core.tools import tool
from PIL import Image

from backend.rag.document_processor import DocumentProcessor
from backend.rag.vector_store import VectorStore
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from weaviate.classes.query import Filter

logger = logging.getLogger(__name__)


def _load_and_scale(image_path: str, max_px: int) -> str:
    """Load a page image from disk, resize so longest side ≤ max_px (proportional), return base64."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    longest = max(w, h)
    if longest > max_px:
        scale = max_px / longest
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


@tool
def rag_retrieve(query: str, doc_ids: List[str], max_px: int = 780) -> List[dict]:
    """
    Search the course material for pages relevant to `query`.

    Args:
        query:   The question or topic to search for.
        doc_ids: List of Upload IDs (= Weaviate doc_ids) to restrict the search to.
        max_px:  Maximum pixel size for the longest dimension of each page image.
                 Use smaller values (e.g. 512) for simple text questions to save
                 context space; use larger values (e.g. 900) when fine visual
                 detail matters (diagrams, equations, charts).

    Returns:
        A list of dicts, each containing:
          - image_b64: base64-encoded JPEG of the page
          - doc_id: source document id
          - page_number: 0-based page index
          - source: source label from the vector store
    """
    processor = DocumentProcessor()
    store = VectorStore()

    try:
        query_embedding = processor.embed_query(query)

        # Build Weaviate filter: doc_id must be in the provided list
        if len(doc_ids) == 1:
            weaviate_filter = Filter.by_property("doc_id").equal(doc_ids[0])
        else:
            weaviate_filter = Filter.by_property("doc_id").contains_any(doc_ids)

        results = store.semantic_search(
            query_embedding=query_embedding,
            top_k=5,
            filters=weaviate_filter,
        )

        pages = []
        missing = 0
        for r in results:
            try:
                b64 = _load_and_scale(r.image_path, max_px)
            except FileNotFoundError:
                missing += 1
                logger.warning("Page image missing on disk: %s (doc=%s page=%s)", r.image_path, r.doc_id, r.page_number)
                continue  # page image missing — skip
            pages.append({
                "image_b64": b64,
                "doc_id": r.doc_id,
                "page_number": r.page_number,
                "source": r.source,
            })

        if missing:
            logger.warning(
                "rag_retrieve: %d/%d pages skipped — image files missing. "
                "Use /lessons/retry-embed to re-embed the document.",
                missing, len(results),
            )

        return pages

    finally:
        processor.close()
        store.close()


# ─── Query rewriter ───────────────────────────────────────────────────────────

_REWRITE_SYSTEM = (
    "You are a search query optimiser for a vector database that stores PDF course pages.\n"
    "Your only job is to rewrite a user query into one or two short, dense, keyword-rich search phrases "
    "that will maximise retrieval recall from a visual-language embedding model (ColQwen).\n\n"
    "Rules:\n"
    "- Output ONLY the rewritten query. No explanation, no preamble, no bullet points.\n"
    "- Preserve all domain-specific terms exactly.\n"
    "- Expand abbreviations where the full form improves recall.\n"
    "- If the query has multiple sub-questions, join them into one coherent search phrase.\n"
    "- Do NOT make the query more specific than the original — only restructure for search."
)


@tool
def rewrite_query(query: str) -> str:
    """
    Rewrite a user query into a cleaner, denser search phrase optimised for
    vector-store retrieval (ColQwen embeddings over PDF pages).

    Use this tool ONLY when:
    - The query is multi-step and a single search phrase would serve all sub-questions better.
    - The phrasing is conversational / narrative and would produce poor embedding matches.

    Do NOT use this tool to add specificity the user did not provide — if the query is
    genuinely too vague, ask the user directly instead.

    Returns the rewritten search query as a plain string.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _REWRITE_SYSTEM},
            {"role": "user", "content": query},
        ],
        "stream": False,
        "think": False,         # disable thinking for qwen3 — we want fast, direct rewrites
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 128,
        },
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()

        # Defensive strip: remove any <think>...</think> block that leaked through
        import re
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        return cleaned if cleaned else query   # fall back to original if empty
    except Exception as exc:
        # Ollama may be offline — return original query so the agent can still proceed
        return f"[rewrite_failed: {exc}] {query}"


