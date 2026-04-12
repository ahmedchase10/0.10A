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


def change_password(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    current_password: str,
    new_password: str,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if len(new_password) < 8:
        raise AppError("AUTH_WEAK_PASSWORD", "Password must be at least 8 characters.", 400)

    teacher = session.exec(
        select(Teacher).where(Teacher.id == teacher_id)
    ).first()
    if not teacher:
        raise AppError("AUTH_TEACHER_NOT_FOUND", "Teacher not found.", 404)

    if not verify_password(current_password, teacher.password_hash):
        raise AppError("AUTH_INVALID_PASSWORD", "Current password is incorrect.", 401)

    teacher.password_hash = hash_password(new_password)
    session.add(teacher)
    session.commit()

    return {
        "success": True,
        "message": "Password updated successfully.",
    }


def update_profile(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    name: Optional[str] = None,
    initials: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    teacher = session.exec(
        select(Teacher).where(Teacher.id == teacher_id)
    ).first()
    if not teacher:
        raise AppError("AUTH_TEACHER_NOT_FOUND", "Teacher not found.", 404)

    # Update name if provided
    if name is not None:
        clean_name = name.strip()
        if len(clean_name) < 2:
            raise AppError("AUTH_INVALID_NAME", "Name is too short.", 400)
        teacher.name = clean_name

    # Update initials if provided
    if initials is not None:
        if len(initials) > 5 :
            raise AppError("AUTH_INVALID_INITIALS", "Initials cannot be more than 5 characters.", 400)
        clean_initials = initials.strip().upper()[:5]
        if len(clean_initials) < 1:
            raise AppError("AUTH_INVALID_INITIALS", "Initials cannot be empty.", 400)
        teacher.initials = clean_initials

    # Update email if provided
    if email is not None:
        clean_email = _normalize_email(email)
        # Check if email is already in use by another teacher
        existing_teacher = session.exec(
            select(Teacher).where(
                Teacher.email == clean_email,
                Teacher.id != teacher_id,
            )
        ).first()
        if existing_teacher:
            raise AppError("AUTH_EMAIL_ALREADY_USED", "Email is already in use.", 409)
        teacher.email = clean_email

    session.add(teacher)
    session.commit()
    session.refresh(teacher)

    return {
        "success": True,
        "teacher": {
            "id": teacher.id,
            "name": teacher.name,
            "initials": teacher.initials,
            "email": teacher.email,
        },
    }
