from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session

from backend.grades.main import delete_grade, get_class_grades, save_grade
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/classes", tags=["grades"])


class SaveGradeRequest(BaseModel):
    student_id: int
    exam_type_id: int
    value: float


class UpdateGradeRequest(BaseModel):
    value: float


@router.get("/{class_id}/grades")
def get_grades_route(
    class_id: int,
    exam_type_id: Optional[int] = Query(None),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return get_class_grades(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        exam_type_id=exam_type_id,
    )


@router.post("/{class_id}/grades")
def save_grade_route(
    class_id: int,
    payload: SaveGradeRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return save_grade(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        student_id=payload.student_id,
        exam_type_id=payload.exam_type_id,
        value=payload.value,
    )




@router.delete("/{class_id}/grades/{grade_id}")
def delete_grade_route(
    class_id: int,
    grade_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return delete_grade(
        session=session,
        teacher_payload=teacher,
        class_id=class_id,
        grade_id=grade_id,
    )
