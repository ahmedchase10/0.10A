"""
backend/agents/creator_agent/tools.py
---------------------------------------
Tools available to the creator agent:

  get_doc_overviews  — fetch Upload.overview JSONB from Postgres for selected doc IDs
  rag_retrieve       — re-exported from pedagogical_agent.tools (semantic page retrieval)
"""
import logging
from typing import List

from langchain_core.tools import tool

# ── Re-export RAG tool (identical implementation, no duplication) ─────────────
from backend.agents.pedagogical_agent.tools import rag_retrieve  # noqa: F401

logger = logging.getLogger(__name__)


@tool
def get_doc_overviews(doc_ids: List[str]) -> List[dict]:
    """
    Fetch the structured overview of selected lesson documents from the database.

    Call this tool FIRST at the start of every exam generation session to understand
    what topics, sections, and subjects the selected documents cover. This overview
    was pre-generated from the full document text and tells you:
      - The chapters/sections of each document
      - The subsections within each chapter
      - The specific topics covered (e.g. "KNN distance metrics", "Overfitting causes")

    Use the overview to decide:
      1. Which topics to cover in the exam based on the teacher's preferences
      2. What queries to pass to rag_retrieve to get the relevant pages

    Args:
        doc_ids: List of Upload IDs (same IDs used in rag_retrieve).

    Returns:
        List of dicts, each containing:
          - doc_id:        the Upload UUID
          - filename:      original filename
          - overview:      the structured JSON overview (sections/subsections/topics)
                           or null if the overview has not been generated yet
          - overview_ready: bool — False means Ollama preprocessing hasn't run yet
    """
    from sqlmodel import Session, create_engine
    from backend.server.db.dbModels import Upload
    from backend.config import POSTGRES_URL

    engine = create_engine(POSTGRES_URL, echo=False)
    results = []
    try:
        with Session(engine) as session:
            for doc_id in doc_ids:
                upload = session.get(Upload, doc_id)
                if upload is None:
                    logger.warning("get_doc_overviews: Upload %s not found", doc_id)
                    results.append({
                        "doc_id": doc_id,
                        "filename": "unknown",
                        "overview": None,
                        "overview_ready": False,
                    })
                else:
                    results.append({
                        "doc_id": doc_id,
                        "filename": upload.filename,
                        "overview": upload.overview,
                        "overview_ready": upload.overview is not None,
                    })
    finally:
        engine.dispose()

    return results

