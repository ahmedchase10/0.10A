from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from backend.login.main import create_account, login
from backend.server.db.engine import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    initials: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register_route(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
):
    return create_account(
        session,
        name=payload.name,
        email=payload.email,
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
        email=payload.email,
        password=payload.password,
    )
