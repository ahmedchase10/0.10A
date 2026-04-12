from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from backend.students.main import add_student, get_class_students, remove_student
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/classes", tags=["students"])


class AddStudentRequest(BaseModel):
	name: str
	email: str


@router.get("/{class_id}/students")
def get_students_route(
	class_id: int,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return get_class_students(
		session=session,
		teacher_payload=teacher,
		class_id=class_id,
	)


@router.post("/{class_id}/students")
def add_student_route(
	class_id: int,
	payload: AddStudentRequest,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return add_student(
		session=session,
		teacher_payload=teacher,
		class_id=class_id,
		name=payload.name,
		email=payload.email,
	)


@router.delete("/{class_id}/students/{student_id}")
def remove_student_route(
	class_id: int,
	student_id: int,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return remove_student(
		session=session,
		teacher_payload=teacher,
		student_id=student_id,
		class_id=class_id,
	)
