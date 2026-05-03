from sqlmodel import Session, select
from fastapi import HTTPException
from backend.server.db.dbModels import Flags

# 🔁 Adjust these imports to match your actual project structure
from backend.attendance.main import _get_owned_class_or_404, _validate_enrolled_students

def create_flag_service(session: Session, teacher_id: int, class_id: int, student_id: int, reason: str) -> dict:
    """Validate ownership/enrollment, create flag, and return success payload."""
    _get_owned_class_or_404(session, teacher_id=teacher_id, class_id=class_id)
    _validate_enrolled_students(session, class_id=class_id, student_ids=[student_id])

    new_flag = Flags(student_id=student_id, class_id=class_id, reason=reason)
    session.add(new_flag)
    session.commit()
    session.refresh(new_flag)

    return {"message": "Flag created successfully", "flag_id": new_flag.id}


def get_flags_service(session: Session, teacher_id: int, class_id: int, student_id: int) -> list:
    """Validate ownership/enrollment, fetch flags for student, and return ordered list."""
    _get_owned_class_or_404(session, teacher_id=teacher_id, class_id=class_id)
    _validate_enrolled_students(session, class_id=class_id, student_ids=[student_id])

    stmt = select(Flags).where(
        Flags.class_id == class_id,
        Flags.student_id == student_id
    ).order_by(Flags.created_at.desc())

    flags = session.exec(stmt).all()
    return [
        {
            "id": f.id,
            "student_id": f.student_id,
            "class_id": f.class_id,
            "reason": f.reason,
            "created_at": f.created_at.isoformat()
        } for f in flags
    ]


def delete_flag_service(session: Session, teacher_id: int, flag_id: int) -> dict:
    """Validate ownership, delete flag, and return success payload."""
    flag = session.get(Flags, flag_id)
    if not flag:
        raise HTTPException(404, "Flag not found.")

    # Ensure teacher owns the class this flag is tied to
    _get_owned_class_or_404(session, teacher_id=teacher_id, class_id=flag.class_id)

    session.delete(flag)
    session.commit()
    return {"message": "Flag deleted successfully."}