from typing import Tuple, cast

from sqlmodel import Session, select

from backend.classes.access import get_owned_class_or_403
from backend.models import AppError
from backend.server.db.dbModels import ExamType, StudentClass


def validate_grade_access(
    session: Session,
    *,
    teacher_id: int,
    class_id: int,
    student_id: int,
    exam_type_id: int,
) -> Tuple[ExamType, StudentClass]:
    # 1) Teacher must own class from route scope.
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    # 2) Exam type must belong to this class.
    exam_type = session.exec(
        select(ExamType).where(
            ExamType.id == exam_type_id,
            ExamType.class_id == class_id
        )
    ).first()

    if not exam_type:
        raise AppError(
            "GRADES_INVALID_EXAM_TYPE",
            "Exam type does not belong to this class.",
            400,
        )

    # 3) Student must be enrolled in this class.
    enrollment = session.exec(
        select(StudentClass).where(
            StudentClass.class_id == class_id,
            StudentClass.student_id == student_id,
        )
    ).first()
    enrollment = cast(StudentClass | None, enrollment)
    if enrollment is None:
        raise AppError(
            "GRADES_STUDENT_NOT_ENROLLED",
            "Student is not enrolled in this class.",
            400,
        )

