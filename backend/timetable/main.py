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


def bulk_add_timetable_entries(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if not entries:
        raise AppError("TIMETABLE_EMPTY_LIST", "At least one timetable entry is required.", 400)

    created_entries = []
    errors = []

    for idx, entry in enumerate(entries):
        try:
            class_id = entry.get("class_id")
            day_of_week = entry.get("day_of_week")
            start_time = entry.get("start_time")
            end_time = entry.get("end_time")

            # Validate required fields
            if class_id is None or day_of_week is None or not start_time or not end_time:
                errors.append({
                    "index": idx,
                    "error": "Missing required fields (class_id, day_of_week, start_time, end_time)",
                })
                continue

            # Validate day_of_week
            if not (0 <= day_of_week <= 6):
                errors.append({
                    "index": idx,
                    "error": "Day of week must be between 0 (Monday) and 6 (Sunday)",
                })
                continue

            # Validate time formats
            if not _validate_time_format(start_time):
                errors.append({
                    "index": idx,
                    "error": "Start time must be in HH:MM format",
                })
                continue
            if not _validate_time_format(end_time):
                errors.append({
                    "index": idx,
                    "error": "End time must be in HH:MM format",
                })
                continue

            # Validate start_time < end_time
            if _time_to_minutes(start_time) >= _time_to_minutes(end_time):
                errors.append({
                    "index": idx,
                    "error": "Start time must be before end time",
                })
                continue

            # Verify teacher owns the class
            class_record = session.exec(
                select(Class).where(
                    Class.id == class_id,
                    Class.teacher_id == teacher_id,
                )
            ).first()
            if not class_record:
                errors.append({
                    "index": idx,
                    "error": "Class not found or you don't have permission to access it",
                })
                continue

            # Check for duplicates
            existing = session.exec(
                select(Timetable).where(
                    Timetable.class_id == class_id,
                    Timetable.day_of_week == day_of_week,
                    Timetable.start_time == start_time,
                )
            ).first()
            if existing:
                errors.append({
                    "index": idx,
                    "error": "This timetable entry already exists",
                })
                continue

            # Create timetable entry
            timetable_entry = Timetable(
                class_id=class_id,
                teacher_id=teacher_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
            )
            session.add(timetable_entry)
            session.flush()  # Get the ID without committing

            created_entries.append({
                "id": timetable_entry.id,
                "class_id": timetable_entry.class_id,
                "class_name": class_record.name,
                "subject": class_record.subject,
                "day_of_week": timetable_entry.day_of_week,
                "start_time": timetable_entry.start_time,
                "end_time": timetable_entry.end_time,
            })

        except Exception as e:
            errors.append({
                "index": idx,
                "error": str(e),
            })

    # Commit all successful entries
    session.commit()

    return {
        "success": True,
        "created": len(created_entries),
        "failed": len(errors),
        "timetable": created_entries,
        "errors": errors if errors else None,
    }


def get_teacher_timetable(
    session: Session,
    teacher_payload: Dict[str, Any],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    # Get all timetable entries for the teacher with class information
    timetable_records = session.exec(
        select(Timetable, Class)
        .join(Class, Timetable.class_id == Class.id)
        .where(Timetable.teacher_id == teacher_id)
        .order_by(Timetable.day_of_week, Timetable.start_time)
    ).all()

    return {
        "success": True,
        "timetable": [
            {
                "id": tt.id,
                "class_id": tt.class_id,
                "class_name": cls.name,
                "subject": cls.subject,
                "day_of_week": tt.day_of_week,
                "start_time": tt.start_time,
                "end_time": tt.end_time,
                "created_at": tt.created_at,
            }
            for tt, cls in timetable_records
        ],
    }


def bulk_update_timetable_entries(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if not entries:
        raise AppError("TIMETABLE_EMPTY_LIST", "At least one timetable entry is required.", 400)

    updated_entries = []
    errors = []

    for idx, entry in enumerate(entries):
        try:
            timetable_id = entry.get("id")
            day_of_week = entry.get("day_of_week")
            start_time = entry.get("start_time")
            end_time = entry.get("end_time")

            # Validate required fields
            if timetable_id is None or day_of_week is None or not start_time or not end_time:
                errors.append({
                    "index": idx,
                    "error": "Missing required fields (id, day_of_week, start_time, end_time)",
                })
                continue

            # Validate day_of_week
            if not (0 <= day_of_week <= 6):
                errors.append({
                    "index": idx,
                    "error": "Day of week must be between 0 (Monday) and 6 (Sunday)",
                })
                continue

            # Validate time formats
            if not _validate_time_format(start_time):
                errors.append({
                    "index": idx,
                    "error": "Start time must be in HH:MM format",
                })
                continue
            if not _validate_time_format(end_time):
                errors.append({
                    "index": idx,
                    "error": "End time must be in HH:MM format",
                })
                continue

            # Validate start_time < end_time
            if _time_to_minutes(start_time) >= _time_to_minutes(end_time):
                errors.append({
                    "index": idx,
                    "error": "Start time must be before end time",
                })
                continue

            # Get the timetable entry and verify ownership
            timetable_entry = session.exec(
                select(Timetable).where(
                    Timetable.id == timetable_id,
                    Timetable.teacher_id == teacher_id,
                )
            ).first()
            if not timetable_entry:
                errors.append({
                    "index": idx,
                    "error": "Timetable entry not found or you don't have permission to update it",
                })
                continue

            # Check if updating would create a duplicate
            existing = session.exec(
                select(Timetable).where(
                    Timetable.class_id == timetable_entry.class_id,
                    Timetable.day_of_week == day_of_week,
                    Timetable.start_time == start_time,
                    Timetable.id != timetable_id,
                )
            ).first()
            if existing:
                errors.append({
                    "index": idx,
                    "error": "A timetable entry with this schedule already exists for this class",
                })
                continue

            # Update the entry
            timetable_entry.day_of_week = day_of_week
            timetable_entry.start_time = start_time
            timetable_entry.end_time = end_time
            session.add(timetable_entry)
            session.flush()

            # Get class info for response
            class_record = session.exec(
                select(Class).where(Class.id == timetable_entry.class_id)
            ).first()

            updated_entries.append({
                "id": timetable_entry.id,
                "class_id": timetable_entry.class_id,
                "class_name": class_record.name if class_record else None,
                "subject": class_record.subject if class_record else None,
                "day_of_week": timetable_entry.day_of_week,
                "start_time": timetable_entry.start_time,
                "end_time": timetable_entry.end_time,
            })

        except Exception as e:
            errors.append({
                "index": idx,
                "error": str(e),
            })

    # Commit all successful updates
    session.commit()

    return {
        "success": True,
        "updated": len(updated_entries),
        "failed": len(errors),
        "timetable": updated_entries,
        "errors": errors if errors else None,
    }
