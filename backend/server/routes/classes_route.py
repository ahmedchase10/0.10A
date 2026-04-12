from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from backend.classes.main import (
	create_teacher_class,
	delete_teacher_class,
	get_teacher_classes,
	update_teacher_class,
)
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/classes", tags=["classes"])


class CreateClassRequest(BaseModel):
	name: str
	subject: str


class UpdateClassRequest(BaseModel):
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


@router.put("/{class_id}")
def update_class_route(
	class_id: int,
	payload: UpdateClassRequest,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return update_teacher_class(
		session=session,
		teacher_payload=teacher,
		class_id=class_id,
		name=payload.name,
		subject=payload.subject,
	)


@router.delete("/{class_id}")
def delete_class_route(
	class_id: int,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return delete_teacher_class(
		session=session,
		teacher_payload=teacher,
		class_id=class_id,
	)



