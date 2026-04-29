from datetime import date, datetime, timezone
from typing import Any, Optional
import uuid

from sqlalchemy import JSON, UniqueConstraint
from sqlmodel import SQLModel, Field


class Teacher(SQLModel, table=True):
    __tablename__ = "teachers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    initials: str = Field(max_length=5)
    email: str = Field(index=True, unique=True, max_length=150)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Class(SQLModel, table=True):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("teacher_id", "name", "subject", name="uq_class_teacher_name_subject"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=120)
    subject: str = Field(max_length=120)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    color: Optional[str] = Field(default=None, max_length=20)   # hex or css color
    school: Optional[str] = Field(default=None, max_length=150)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Upload(SQLModel, table=True):
    __tablename__ = "uploads"
    __table_args__ = (
        UniqueConstraint("class_id", "file_hash", name="uq_upload_class_hash"),
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_hash: str = Field(index=True, max_length=64)
    size: int
    embedded: bool = Field(default=False)
    overview: Optional[Any] = Field(default=None, sa_type=JSON)  # structured doc overview, null until preprocessed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(index=True, unique=True, max_length=150)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudentClass(SQLModel, table=True):
    __tablename__ = "student_class"

    class_id: int = Field(foreign_key="classes.id", primary_key=True)
    student_id: int = Field(foreign_key="students.id", primary_key=True)
    flagged: bool = Field(default=False)
    flag_reason: str = Field(default="", max_length=500)
    display_name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Timetable(SQLModel, table=True):
    __tablename__ = "timetable"
    __table_args__ = (
        UniqueConstraint("class_id", "day_of_week", "start_time", name="uq_timetable_class_day_time"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    day_of_week: int = Field(ge=0, le=6)  # 0 = Monday, 6 = Sunday
    start_time: str = Field(max_length=5)  # HH:MM format
    end_time: str = Field(max_length=5)  # HH:MM format
    classroom: Optional[str] = Field(default=None, max_length=100)  # e.g. "Room 12"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", "session_date", name="uq_attendance_class_student_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    session_date: date = Field(index=True)
    present: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExamType(SQLModel, table=True):
    __tablename__ = "exam_types"
    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_exam_type_class_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    name: str = Field(max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Grade(SQLModel, table=True):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("student_id", "exam_type_id", name="uq_grade_student_exam_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    exam_type_id: int = Field(foreign_key="exam_types.id", index=True)
    value: float


class AgentSession(SQLModel, table=True):
    __tablename__ = "agent_sessions"

    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    title: str = Field(max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Grading Agent ────────────────────────────────────────────────────────────

class ExamPaper(SQLModel, table=True):
    """Class-scoped exam question paper. Uploaded before analysis. Separate from student answer PDFs."""
    __tablename__ = "exam_papers"
    __table_args__ = (
        UniqueConstraint("class_id", "file_hash", name="uq_exam_paper_class_hash"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)   # uploads/exam_papers/{teacher_id}/{uuid}.pdf
    file_hash: str = Field(index=True, max_length=64)
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExamUpload(SQLModel, table=True):
    """Student exam PDFs — separate from Upload, never embedded in Weaviate."""
    __tablename__ = "exam_uploads"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)   # uploads/exams/{teacher_id}/{uuid}.pdf
    file_hash: str = Field(index=True, max_length=64)
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GradingBlueprint(SQLModel, table=True):
    """Teacher-scoped reusable correction blueprint. Not tied to any class."""
    __tablename__ = "grading_blueprints"

    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    title: str = Field(max_length=120)
    analysis_thread_id: str = Field(default="", max_length=36)  # LangGraph thread for blueprint run
    exam_paper_id: Optional[int] = Field(default=None, foreign_key="exam_papers.id", index=True)  # display ref
    lesson_doc_ids: str = Field(default="[]")           # JSON array of Upload UUIDs
    exam_file_path: str = Field(max_length=512)         # absolute path used by agent (survives paper deletion)
    correction_file_path: Optional[str] = Field(default=None, max_length=512)  # null after analysis
    preferences: str = Field(default="")               # teacher's grading criteria text
    style_guide: str = Field(default="")               # essay / math style notes
    blueprint_json: str = Field(default="")            # structured Q/criteria JSON from agent
    deleted: bool = Field(default=False)               # soft-delete; checkpoint is hard-deleted
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GradingSession(SQLModel, table=True):
    """One grading session per student per batch run."""
    __tablename__ = "grading_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    blueprint_id: int = Field(foreign_key="grading_blueprints.id", index=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    exam_type_id: int = Field(foreign_key="exam_types.id", index=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    exam_upload_id: str = Field(foreign_key="exam_uploads.id", index=True)
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True)  # LangGraph checkpoint
    batch_id: str = Field(index=True, max_length=36)   # groups all sessions from one /grade call
    queue_position: int = Field(default=0)              # sort order within batch (alphabetical by student name)
    status: str = Field(default="pending")              # pending | reviewing | approved | cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GradingQuestionResult(SQLModel, table=True):
    """Per-question grading outcome, written when teacher approves or edits."""
    __tablename__ = "grading_question_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="grading_sessions.id", index=True)
    question_number: int
    question_label: str = Field(max_length=20)      # e.g. "Q1a"
    max_points: float
    awarded_points: float
    reasoning: str = Field(default="")
    teacher_override: bool = Field(default=False)   # True if teacher edited the agent's score


# ─── Creator Agent ────────────────────────────────────────────────────────────

class GeneratedExam(SQLModel, table=True):
    """Teacher-scoped generated exam. Stores the agent session + final exam JSON."""
    __tablename__ = "generated_exams"

    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True, max_length=36)
    title: str = Field(max_length=120)
    doc_ids: str = Field(default="[]")        # JSON array of Upload UUIDs
    preferences: str = Field(default="{}")    # full preferences JSON string
    exam_json: str = Field(default="")        # final exam JSON produced by agent
    loop_count: int = Field(default=0)        # how many evaluator loops ran (0, 1, or 2)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProcessingJob(SQLModel, table=True):
    __tablename__ = "processing_jobs"

    file_hash: str = Field(primary_key=True, max_length=64, index=True)  # SHA256
    embedding_in_progress: bool = Field(default=False)
    overview_in_progress: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = [
    "SQLModel",
    "Teacher",
    "Class",
    "Upload",
    "Student",
    "StudentClass",
    "Timetable",
    "Attendance",
    "ExamType",
    "Grade",
    "AgentSession",
    "ExamPaper",
    "ExamUpload",
    "GradingBlueprint",
    "GradingSession",
    "GradingQuestionResult",
    "GeneratedExam",
    "ProcessingJob",
]
