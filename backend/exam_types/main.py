from typing import Any, Dict

from sqlalchemy import desc
from sqlmodel import Session, select

from backend.classes.access import get_owned_class_or_403
from backend.models import AppError
from backend.server.db.dbModels import ExamType

def _clean_text(value: str) -> str:
    return " ".join(value.strip().lower().split())



def get_exam_types_for_class(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    rows = session.exec(
        select(ExamType)
        .where(ExamType.class_id == class_id)
        .order_by(desc(ExamType.created_at), desc(ExamType.id))
    ).all()

    return {
        "success": True,
        "exam_types": [
            {
                "id": row.id,
                "class_id": row.class_id,
                "name": row.name,
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }


def create_exam_type(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    name: str,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    clean_name = _clean_text(name)

    if len(clean_name) < 2:
        raise AppError(
            "EXAM_TYPE_INVALID_NAME",
            "Exam type name is too short.",
            400,
        )

    # enforce uniqueness per class (case-safe)
    existing = session.exec(
        select(ExamType).where(
            ExamType.class_id == class_id,
            ExamType.name == clean_name,
        )
    ).first()

    if existing:
        raise AppError(
            "EXAM_TYPE_ALREADY_EXISTS",
            "Exam type already exists for this class.",
            409,
        )

    row = ExamType(
        class_id=class_id,
        name=clean_name,
    )

    session.add(row)
    session.commit()
    session.refresh(row)

    return {
        "success": True,
        "exam_type": {
            "id": row.id,
            "class_id": row.class_id,
            "name": row.name,
            "created_at": row.created_at,
        },
    }


def delete_exam_type(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    exam_type_id: int,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    row = session.exec(
        select(ExamType).where(
            ExamType.id == exam_type_id,
            ExamType.class_id == class_id,
        )
    ).first()

    if not row:
        raise AppError(
            "EXAM_TYPE_NOT_FOUND",
            "Exam type not found for this class.",
            404,
        )

    session.delete(row)
    session.commit()

    return {
        "success": True,
        "deleted": {
            "id": exam_type_id,
            "class_id": class_id,
        },
    }