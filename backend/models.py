# =============================================
# DIGI-SCHOOL AI — Data Models
# =============================================

from dataclasses import dataclass, field
from typing import Optional, List, Any, Literal
from datetime import datetime, date
from pydantic import BaseModel ,Field


# ─── Existing RAG models (unchanged) ─────────

@dataclass
class Document:
    """Represents an uploaded PDF document"""
    filename: str
    source: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    doc_id: Optional[str] = None
    total_pages: int = 0


@dataclass
class Page:
    """Represents one page of a PDF after processing"""
    doc_id: str
    page_number: int
    image_path: str
    source: str
    embedding: Optional[list] = None
    content_description: Optional[str] = None


@dataclass
class SearchResult:
    """Represents one result from Weaviate search"""
    doc_id: str
    page_number: int
    score: float
    image_path: str
    source: str


@dataclass
class Message:
    """One turn in a conversation"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)



class ApiMessage(BaseModel):
    """Message format for API communication (Node.js ↔ FastAPI)"""

    message: str
    role: str
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class AppError(Exception):
    """Shared API exception shape used across backend modules."""
    code: str
    message: str
    status_code: int = 400
