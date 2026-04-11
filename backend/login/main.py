from typing import Any, Dict, Optional

import bcrypt
from sqlmodel import Session, select

from backend.models import AppError
from backend.server.auth.jwt import create_token
from backend.server.db.dbModels import Teacher


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def _teacher_payload(teacher: Teacher) -> Dict[str, Any]:
    return {
        "id": teacher.id,
        "name": teacher.name,
        "email": teacher.email,
    }


def create_account(
    session: Session,
    *,
    name: str,
    email: str,
    password: str,
    initials: Optional[str] = None,
) -> Dict[str, Any]:
    clean_email = _normalize_email(email)
    clean_name = name.strip()

    if len(clean_name) < 2:
        raise AppError("AUTH_INVALID_NAME", "Name is too short.", 400)
    if len(password) < 8:
        raise AppError("AUTH_WEAK_PASSWORD", "Password must be at least 8 characters.", 400)

    existing_teacher = session.exec(
        select(Teacher).where(Teacher.email == clean_email)
    ).first()
    if existing_teacher:
        raise AppError("AUTH_EMAIL_ALREADY_USED", "Email is already in use.", 409)

    teacher = Teacher(
        name=clean_name,
        initials=(initials or clean_name[:2]).upper()[:5],
        email=clean_email,
        password_hash=hash_password(password),
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)

    teacher_payload = _teacher_payload(teacher)
    token = create_token(teacher_payload)
    return {
        "success": True,
        "token": token,
        "teacher": teacher_payload,
    }


def login(
    session: Session,
    *,
    email: str,
    password: str,
) -> Dict[str, Any]:
    clean_email = _normalize_email(email)

    teacher = session.exec(
        select(Teacher).where(Teacher.email == clean_email)
    ).first()

    if teacher is None or not verify_password(password, teacher.password_hash):
        raise AppError("AUTH_INVALID_CREDENTIALS", "Invalid email or password.", 401)

    teacher_payload = _teacher_payload(teacher)
    token = create_token(teacher_payload)
    return {
        "success": True,
        "token": token,
        "teacher": teacher_payload,
    }
