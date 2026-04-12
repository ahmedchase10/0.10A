from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from backend.classes.main import create_teacher_class, get_teacher_classes
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/classes", tags=["classes"])


class CreateClassRequest(BaseModel):
	name: str
	subject: str


@router.get("")
def get_classes_route(
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return get_teacher_classes(session=session, teacher_payload=teacher)


@router.post("")
def create_class_route(
	payload: CreateClassRequest,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return create_teacher_class(
		session=session,
		teacher_payload=teacher,
		name=payload.name,
		subject=payload.subject,
	)

