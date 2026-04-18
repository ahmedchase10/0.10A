from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from backend.exam_types.main import create_exam_type, delete_exam_type, get_exam_types_for_class
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/classes", tags=["exam-types"])


class CreateExamTypeRequest(BaseModel):
    name: str


@router.get("/{class_id}/exam-types")
def get_exam_types_route(
    class_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return get_exam_types_for_class(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
    )


@router.post("/{class_id}/exam-types")
def create_exam_type_route(
    class_id: int,
    payload: CreateExamTypeRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return create_exam_type(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        name=payload.name,
    )


@router.delete("/{class_id}/exam-types/{exam_type_id}")
def delete_exam_type_route(
    class_id: int,
    exam_type_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return delete_exam_type(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        exam_type_id=exam_type_id,
    )

