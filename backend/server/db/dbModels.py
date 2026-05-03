from datetime import date, datetime, timezone
from typing import Any, Optional, List
import uuid

from sqlalchemy import JSON, UniqueConstraint, Column, Integer, ForeignKey
from sqlmodel import SQLModel, Field, Relationship, String


class Teacher(SQLModel, table=True):
    __tablename__ = "teachers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    initials: str = Field(max_length=5)
    email: str = Field(index=True, unique=True, max_length=150)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    classes: List["Class"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    timetables: List["Timetable"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    agent_sessions: List["AgentSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    exam_papers: List["ExamPaper"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    exam_uploads: List["ExamUpload"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    grading_blueprints: List["GradingBlueprint"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    generated_exams: List["GeneratedExam"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    email_credentials: List["UserEmailCredentials"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class Class(SQLModel, table=True):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("teacher_id", "name", "subject", name="uq_class_teacher_name_subject"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=120)
    subject: str = Field(max_length=120)
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    color: Optional[str] = Field(default=None, max_length=20)
    school: Optional[str] = Field(default=None, max_length=150)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    uploads: List["Upload"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    student_classes: List["StudentClass"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    flags: List["Flags"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    timetables: List["Timetable"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    attendances: List["Attendance"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    exam_types: List["ExamType"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    agent_sessions: List["AgentSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    exam_papers: List["ExamPaper"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    grading_sessions: List["GradingSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class Upload(SQLModel, table=True):
    __tablename__ = "uploads"
    __table_args__ = (
        UniqueConstraint("class_id", "file_hash", name="uq_upload_class_hash"),
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_hash: str = Field(index=True, max_length=64)
    size: int
    embedded: bool = Field(default=False)
    overview: Optional[Any] = Field(default=None, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(index=True, unique=True, max_length=150)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    student_classes: List["StudentClass"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    flags: List["Flags"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    attendances: List["Attendance"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    grades: List["Grade"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    grading_sessions: List["GradingSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class StudentClass(SQLModel, table=True):
    __tablename__ = "student_class"

    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True))
    student_id: int = Field(sa_column=Column(Integer, ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True))
    display_name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Flags(SQLModel, table=True):
    __tablename__ = "flags"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(sa_column=Column(Integer, ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    reason: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Timetable(SQLModel, table=True):
    __tablename__ = "timetable"
    __table_args__ = (
        UniqueConstraint("class_id", "day_of_week", "start_time", name="uq_timetable_class_day_time"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = Field(max_length=5)
    end_time: str = Field(max_length=5)
    classroom: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", "session_date", name="uq_attendance_class_student_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    student_id: int = Field(sa_column=Column(Integer, ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    session_date: date = Field(index=True)
    present: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExamType(SQLModel, table=True):
    __tablename__ = "exam_types"
    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_exam_type_class_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    name: str = Field(max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    grades: List["Grade"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})
    grading_sessions: List["GradingSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class Grade(SQLModel, table=True):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("student_id", "exam_type_id", name="uq_grade_student_exam_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(sa_column=Column(Integer, ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    exam_type_id: int = Field(sa_column=Column(Integer, ForeignKey("exam_types.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    value: float


class AgentSession(SQLModel, table=True):
    __tablename__ = "agent_sessions"

    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    title: str = Field(max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExamPaper(SQLModel, table=True):
    __tablename__ = "exam_papers"
    __table_args__ = (
        UniqueConstraint("class_id", "file_hash", name="uq_exam_paper_class_hash"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_hash: str = Field(index=True, max_length=64)
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExamUpload(SQLModel, table=True):
    __tablename__ = "exam_uploads"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_hash: str = Field(index=True, max_length=64)
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    grading_sessions: List["GradingSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class GradingBlueprint(SQLModel, table=True):
    __tablename__ = "grading_blueprints"

    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    title: str = Field(max_length=120)
    analysis_thread_id: str = Field(default="", max_length=36)
    exam_paper_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("exam_papers.id", ondelete="SET NULL", onupdate="CASCADE"), index=True))
    lesson_doc_ids: str = Field(default="[]")
    exam_file_path: str = Field(max_length=512)
    correction_file_path: Optional[str] = Field(default=None, max_length=512)
    preferences: str = Field(default="")
    style_guide: str = Field(default="")
    blueprint_json: str = Field(default="")
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    grading_sessions: List["GradingSession"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class GradingSession(SQLModel, table=True):
    __tablename__ = "grading_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    blueprint_id: int = Field(sa_column=Column(Integer, ForeignKey("grading_blueprints.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    class_id: int = Field(sa_column=Column(Integer, ForeignKey("classes.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    exam_type_id: int = Field(sa_column=Column(Integer, ForeignKey("exam_types.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    student_id: int = Field(sa_column=Column(Integer, ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    exam_upload_id: str = Field(sa_column=Column(String, ForeignKey("exam_uploads.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True)
    batch_id: str = Field(index=True, max_length=36)
    queue_position: int = Field(default=0)
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    question_results: List["GradingQuestionResult"] = Relationship(sa_relationship_kwargs={"passive_deletes": True})


class GradingQuestionResult(SQLModel, table=True):
    __tablename__ = "grading_question_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(sa_column=Column(String, ForeignKey("grading_sessions.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    question_number: int
    question_label: str = Field(max_length=20)
    max_points: float
    awarded_points: float
    reasoning: str = Field(default="")
    teacher_override: bool = Field(default=False)


class GeneratedExam(SQLModel, table=True):
    __tablename__ = "generated_exams"

    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), index=True))
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True, max_length=36)
    title: str = Field(max_length=120)
    doc_ids: str = Field(default="[]")
    preferences: str = Field(default="{}")
    exam_json: str = Field(default="")
    loop_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProcessingJob(SQLModel, table=True):
    __tablename__ = "processing_jobs"

    file_hash: str = Field(primary_key=True, max_length=64, index=True)
    embedding_in_progress: bool = Field(default=False)
    overview_in_progress: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserEmailCredentials(SQLModel, table=True):
    __tablename__ = "user_email_credentials"

    user_id: int = Field(sa_column=Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True))
    email: str = Field(primary_key=True)
    access_token: Optional[str] = Field(default=None)
    refresh_token: Optional[str] = Field(default=None)
    token_expiry: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = [
    "SQLModel", "Teacher", "Class", "Upload", "Student", "StudentClass",
    "Flags", "Timetable", "Attendance", "ExamType", "Grade", "AgentSession",
    "ExamPaper", "ExamUpload", "GradingBlueprint", "GradingSession",
    "GradingQuestionResult", "GeneratedExam", "ProcessingJob", "UserEmailCredentials",
]