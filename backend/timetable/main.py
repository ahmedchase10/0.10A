import re
from typing import Any, Dict, List

from sqlmodel import Session, select

from backend.models import AppError
from backend.server.db.dbModels import Class, Timetable


def _validate_time_format(time_str: str) -> bool:
    """Validate HH:MM format (00:00 to 23:59)"""
    pattern = r'^([01][0-9]|2[0-3]):([0-5][0-9])$'
    return bool(re.match(pattern, time_str))


def _time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes since midnight"""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


def _serialize_entry(tt: Timetable, cls: Class) -> Dict[str, Any]:
    return {
        "id": tt.id,
        "class_id": tt.class_id,
        "class_name": cls.name,
        "subject": cls.subject,
        "day_of_week": tt.day_of_week,
        "start_time": tt.start_time,
        "end_time": tt.end_time,
        "classroom": tt.classroom,
        "created_at": tt.created_at,
    }


def _validate_entry(entry: Dict[str, Any]) -> None:
    """Raise AppError if the entry fields are invalid."""
    class_id = entry.get("class_id")
    day_of_week = entry.get("day_of_week")
    start_time = entry.get("start_time")
    end_time = entry.get("end_time")

    if class_id is None or day_of_week is None or not start_time or not end_time:
        raise AppError("TIMETABLE_MISSING_FIELDS", "class_id, day_of_week, start_time and end_time are required.", 400)

    if not (0 <= day_of_week <= 6):
        raise AppError("TIMETABLE_INVALID_DAY", "day_of_week must be between 0 (Monday) and 6 (Sunday).", 400)

    if not _validate_time_format(start_time):
        raise AppError("TIMETABLE_INVALID_TIME", f"start_time '{start_time}' must be HH:MM.", 400)

    if not _validate_time_format(end_time):
        raise AppError("TIMETABLE_INVALID_TIME", f"end_time '{end_time}' must be HH:MM.", 400)

    if _time_to_minutes(start_time) >= _time_to_minutes(end_time):
        raise AppError("TIMETABLE_INVALID_RANGE", "start_time must be before end_time.", 400)


def _upsert_single(
    session: Session,
    teacher_id: int,
    entry: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate, check ownership, then insert or update one timetable slot."""
    _validate_entry(entry)

    class_id   = entry["class_id"]
    day_of_week = entry["day_of_week"]
    start_time  = entry["start_time"]
    end_time    = entry["end_time"]
    classroom   = entry.get("classroom")

    class_record = session.exec(
        select(Class).where(Class.id == class_id, Class.teacher_id == teacher_id)
    ).first()
    if not class_record:
        raise AppError("TIMETABLE_CLASS_NOT_FOUND", f"Class {class_id} not found or not yours.", 404)

    existing = session.exec(
        select(Timetable).where(
            Timetable.class_id == class_id,
            Timetable.day_of_week == day_of_week,
            Timetable.start_time == start_time,
        )
    ).first()

    if existing:
        existing.end_time  = end_time
        existing.classroom = classroom
        session.add(existing)
        session.flush()
        return _serialize_entry(existing, class_record)

    new_entry = Timetable(
        class_id=class_id,
        teacher_id=teacher_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        classroom=classroom,
    )
    session.add(new_entry)
    session.flush()
    return _serialize_entry(new_entry, class_record)


def bulk_upsert_timetable_entries(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Insert or update timetable entries. Natural key: (class_id, day_of_week, start_time)."""
    teacher_id = int(teacher_payload["id"])

    if not entries:
        raise AppError("TIMETABLE_EMPTY_LIST", "At least one timetable entry is required.", 400)

    upserted = [_upsert_single(session, teacher_id, entry) for entry in entries]
    session.commit()

    return {"success": True, "upserted": len(upserted), "timetable": upserted}


def get_teacher_timetable(
    session: Session,
    teacher_payload: Dict[str, Any],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    rows = session.exec(
        select(Timetable, Class)
        .join(Class, Timetable.class_id == Class.id)
        .where(Timetable.teacher_id == teacher_id)
        .order_by(Timetable.day_of_week, Timetable.start_time)
    ).all()

    return {
        "success": True,
        "timetable": [_serialize_entry(tt, cls) for tt, cls in rows],
    }


def delete_timetable_entry(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    timetable_id: int,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    entry = session.exec(
        select(Timetable).where(
            Timetable.id == timetable_id,
            Timetable.teacher_id == teacher_id,
        )
    ).first()
    if not entry:
        raise AppError("TIMETABLE_NOT_FOUND", "Timetable entry not found or not yours.", 404)

    session.delete(entry)
    session.commit()

    return {"success": True, "message": "Timetable entry deleted."}
