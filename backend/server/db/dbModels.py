from datetime import date, datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import UniqueConstraint
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
]
