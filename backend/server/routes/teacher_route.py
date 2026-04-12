from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from backend.teacher.main import change_password, create_account, login, update_profile
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/auth", tags=["auth"])
teachers_router = APIRouter(prefix="/teachers", tags=["teachers"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    initials: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register_route(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
):
    return create_account(
        session,
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
        initials=payload.initials,
    )


@router.post("/login")
def login_route(
    payload: LoginRequest,
    session: Session = Depends(get_session),
):
    return login(
        session,
        email=str(payload.email),
        password=payload.password,
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    initials: Optional[str] = None
    email: Optional[EmailStr] = None


@teachers_router.put("/password")
def change_password_route(
    payload: ChangePasswordRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return change_password(
        session=session,
        teacher_payload=teacher,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )


@teachers_router.patch("/profile")
def update_profile_route(
    payload: UpdateProfileRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return update_profile(
        session=session,
        teacher_payload=teacher,
        name=payload.name,
        initials=payload.initials,
        email=str(payload.email) if payload.email else None,
    )
