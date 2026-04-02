# =============================================
# DIGI-SCHOOL AI — Data Models
# =============================================

from dataclasses import dataclass, field
from typing import Optional, List, Any, Literal
from datetime import datetime, date
from pydantic import BaseModel


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


# ─── Agent request/response (Pydantic — used by FastAPI) ─────

class TeacherContext(BaseModel):
    """Teacher info forwarded from Node.js"""
    id:    int
    name:  str
    email: str


class ClassInfo(BaseModel):
    id:     int
    name:   str
    period: Optional[str] = None
    room:   Optional[str] = None


class StudentInfo(BaseModel):
    id:         int
    name:       str
    class_id:   int
    class_name: str


class RequestContext(BaseModel):
    """Full context forwarded from Node.js with every agent call"""
    classes:  List[ClassInfo]
    students: List[StudentInfo]
    date:     str   # ISO format: "2026-03-30"


class AgentRequest(BaseModel):
    """Body received at POST /agent/run"""
    input:   str
    teacher: TeacherContext
    context: RequestContext


# ─── Agent action types ───────────────────────

AttendanceStatus = Literal["P", "A", "L", "E"]


class AttendanceAction(BaseModel):
    """A single attendance record the agent wants to write"""
    student_id: int
    student_name: str
    class_id:   int
    class_name: str
    status:     AttendanceStatus
    date:       str


class FlagAction(BaseModel):
    """A student the agent wants to flag"""
    student_id:   int
    student_name: str
    class_id:     int
    type:         Literal["behavior", "absence", "grade"]
    reason:       str


class HomeworkAction(BaseModel):
    """Homework the agent wants to log"""
    class_id:      int
    class_name:    str
    title:         str
    subject:       Optional[str] = None
    chapter:       Optional[str] = None
    assigned_date: str
    due_date:      Optional[str] = None


class LessonAction(BaseModel):
    """Lesson log entry the agent wants to write"""
    class_id:   int
    class_name: str
    date:       str
    chapter:    Optional[str] = None
    topic:      Optional[str] = None
    weak_point: Optional[str] = None
    insight:    Optional[str] = None


class AgentAction(BaseModel):
    """One action extracted and executed by the agent"""
    type:        Literal["attendance", "flag", "homework", "lesson", "insight"]
    description: str                 # human-readable summary shown in UI
    data:        Any                 # one of the action models above


class AgentResponse(BaseModel):
    """Shape returned to Node.js after agent run"""
    summary:  str                    # one sentence shown in the agent bar
    actions:  List[AgentAction]      # list of all actions taken
    raw:      Optional[Any] = None   # full LangGraph state (debug)