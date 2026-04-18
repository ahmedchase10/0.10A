from typing import Any, Dict, Optional

from sqlmodel import Session, select

from backend.classes.access import get_owned_class_or_403
from backend.grades.access import validate_grade_access
from backend.models import AppError
from backend.server.db.dbModels import ExamType, Grade, StudentClass


def get_class_grades(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    exam_type_id: Optional[int] = None,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    query = (
        select(Grade, StudentClass, ExamType)
        .join(ExamType, ExamType.id == Grade.exam_type_id)
        .join(
            StudentClass,
            (StudentClass.class_id == ExamType.class_id)
            & (StudentClass.student_id == Grade.student_id),
        )
        .where(ExamType.class_id == class_id)
        .order_by(StudentClass.display_name)
    )

    if exam_type_id is not None:
        query = query.where(Grade.exam_type_id == exam_type_id)

    rows = session.exec(query).all()

    return {
        "success": True,
        "grades": [
            {
                "id": grade.id,
                "class_id": exam_type.class_id,
                "student_id": grade.student_id,
                "student_name": student_class.display_name,
                "exam_type_id": grade.exam_type_id,
                "exam_type_name": exam_type.name,
                "value": grade.value,
            }
            for grade, student_class, exam_type in rows
        ],
    }


def save_grade(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    student_id: int,
    exam_type_id: int,
    value: float,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if not (0 <= value <= 20):
        raise AppError("GRADES_INVALID_VALUE", "Grade value must be between 0 and 20.", 400)

    validate_grade_access(
        session,
        teacher_id=teacher_id,
        class_id=class_id,
        student_id=student_id,
        exam_type_id=exam_type_id,
    )

    existing = session.exec(
        select(Grade).where(
            Grade.student_id == student_id,
            Grade.exam_type_id == exam_type_id,
        )
    ).first()

    if existing:
        existing.value = value
        session.add(existing)
        session.commit()
        session.refresh(existing)
        grade_row = existing
        operation = "updated"
    else:
        grade_row = Grade(
            student_id=student_id,
            exam_type_id=exam_type_id,
            value=value,
        )
        session.add(grade_row)
        session.commit()
        session.refresh(grade_row)
        operation = "created"

    return {
        "success": True,
        "operation": operation,
        "grade": {
            "id": grade_row.id,
            "class_id": class_id,
            "student_id": grade_row.student_id,
            "exam_type_id": grade_row.exam_type_id,
            "value": grade_row.value,
        },
    }


def delete_grade(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    grade_id: int,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    get_owned_class_or_403(
        session,
        teacher_id=teacher_id,
        class_id=class_id,
    )

    grade_row = session.exec(
        select(Grade)
        .join(ExamType, ExamType.id == Grade.exam_type_id)
        .where(
            Grade.id == grade_id,
            ExamType.class_id == class_id,
        )
    ).first()

    if not grade_row:
        raise AppError(
            "GRADES_NOT_FOUND",
            "Grade not found for this class.",
            404,
        )

    session.delete(grade_row)
    session.commit()

    return {
        "success": True,
        "deleted": {
            "id": grade_id,
            "class_id": class_id,
        },
    }