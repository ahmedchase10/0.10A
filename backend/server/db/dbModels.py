from datetime import datetime, timezone
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


class Upload(SQLModel, table=True):
    __tablename__ = "uploads"
    __table_args__ = (
        UniqueConstraint("teacher_id", "file_hash", name="uq_upload_teacher_hash"),
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    teacher_id: int = Field(foreign_key="teachers.id", index=True)
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_hash: str = Field(index=True, max_length=64)
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["SQLModel", "Teacher", "Upload"]
