from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Document:
    """Represents an uploaded PDF document"""
    filename: str
    source: str              # "local" or "classroom"
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
    content_description: Optional[str] = None  # ← optional text summary of page

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

@dataclass
class ChatSession:
    """Full conversation history for a teacher session"""
    session_id: str
    messages: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))

    def get_history(self):
        return [{"role": m.role, "content": m.content} for m in self.messages]