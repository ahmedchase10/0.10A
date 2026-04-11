from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional


class Teacher(SQLModel, table=True):
    __tablename__ = "teachers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    initials: str = Field(max_length=5)
    email: str = Field(index=True, unique=True, max_length=150)
    password_hash: str
    subject: Optional[str] = Field(default=None, max_length=100)
    school: Optional[str] = Field(default=None, max_length=150)
    grades: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["SQLModel", "Teacher"]
