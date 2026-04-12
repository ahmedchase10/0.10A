from sqlmodel import Session, select

from backend.models import AppError
from backend.server.db.dbModels import Class


def get_owned_class_or_403(
    session: Session,
    *,
    teacher_id: int,
    class_id: int,
) -> Class:
    class_row = session.exec(select(Class).where(Class.id == class_id)).first()
    if class_row is None:
        raise AppError("LESSONS_CLASS_NOT_FOUND", "Class not found.", 404)
    if class_row.teacher_id != teacher_id:
        raise AppError("LESSONS_CLASS_FORBIDDEN", "You do not teach this class.", 403)
    return class_row

