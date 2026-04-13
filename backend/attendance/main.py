from datetime import date
from typing import Any, Dict, List

from sqlmodel import Session, select

from backend.models import AppError
from backend.server.db.dbModels import Attendance, Class, StudentClass


def _get_owned_class_or_404(session: Session, *, teacher_id: int, class_id: int) -> Class:
    class_record = session.exec(
        select(Class).where(
            Class.id == class_id,
            Class.teacher_id == teacher_id,
        )
    ).first()
    if not class_record:
        raise AppError(
            "CLASSES_NOT_FOUND",
            "Class not found or you don't have permission to access it.",
            404,
        )
    return class_record


def _validate_enrolled_students(
    session: Session,
    *,
    class_id: int,
    student_ids: List[int],
) -> List[int]:
    unique_student_ids = list(dict.fromkeys(student_ids))

    enrolled_student_ids = set(
        session.exec(
            select(StudentClass.student_id).where(
                StudentClass.class_id == class_id,
                StudentClass.student_id.in_(unique_student_ids),
            )
        ).all()
    )
    invalid_student_ids = [student_id for student_id in unique_student_ids if student_id not in enrolled_student_ids]
    if invalid_student_ids:
        raise AppError(
            "ATTENDANCE_STUDENT_NOT_ENROLLED",
            f"Students are not enrolled in this class: {invalid_student_ids}",
            400,
        )

    return unique_student_ids


def create_attendance_records(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    session_date: date,
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if not records:
        raise AppError("ATTENDANCE_EMPTY_RECORDS", "At least one attendance record is required.", 400)

    _get_owned_class_or_404(session, teacher_id=teacher_id, class_id=class_id)

    unique_student_ids = _validate_enrolled_students(
        session,
        class_id=class_id,
        student_ids=[int(record["student_id"]) for record in records],
    )

    existing_rows = session.exec(
        select(Attendance).where(
            Attendance.class_id == class_id,
            Attendance.session_date == session_date,
            Attendance.student_id.in_(unique_student_ids),
        )
    ).all()
    existing_by_student = {row.student_id: row for row in existing_rows}

    created = 0
    updated = 0
    for record in records:
        student_id = int(record["student_id"])
        present = bool(record["present"])

        existing = existing_by_student.get(student_id)
        if existing:
            existing.present = present
            session.add(existing)
            updated += 1
            continue

        attendance_row = Attendance(
            class_id=class_id,
            student_id=student_id,
            session_date=session_date,
            present=present,
        )
        session.add(attendance_row)
        created += 1

    session.commit()

    rows = session.exec(
        select(Attendance).where(
            Attendance.class_id == class_id,
            Attendance.session_date == session_date,
            Attendance.student_id.in_(unique_student_ids),
        )
    ).all()

    return {
        "success": True,
        "class_id": class_id,
        "session_date": session_date,
        "created": created,
        "updated": updated,
        "attendance": [
            {
                "id": row.id,
                "student_id": row.student_id,
                "present": row.present,
            }
            for row in rows
        ],
    }


def get_attendance_records(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    session_date: date,
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    _get_owned_class_or_404(session, teacher_id=teacher_id, class_id=class_id)

    rows = session.exec(
        select(Attendance, StudentClass)
        .join(
            StudentClass,
            (StudentClass.class_id == Attendance.class_id)
            & (StudentClass.student_id == Attendance.student_id),
        )
        .where(
            Attendance.class_id == class_id,
            Attendance.session_date == session_date,
        )
        .order_by(StudentClass.display_name, Attendance.student_id)
    ).all()

    return {
        "success": True,
        "teacher_id": teacher_id,
        "class_id": class_id,
        "session_date": session_date,
        "attendance": [
            {
                "id": attendance.id,
                "student_id": attendance.student_id,
                "student_name": student_class.display_name,
                "present": attendance.present,
            }
            for attendance, student_class in rows
        ],
    }


def update_attendance_presence(
    session: Session,
    teacher_payload: Dict[str, Any],
    *,
    class_id: int,
    session_date: date,
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    teacher_id = int(teacher_payload["id"])

    if not records:
        raise AppError("ATTENDANCE_EMPTY_RECORDS", "At least one attendance record is required.", 400)

    _get_owned_class_or_404(session, teacher_id=teacher_id, class_id=class_id)

    unique_student_ids = _validate_enrolled_students(
        session,
        class_id=class_id,
        student_ids=[int(record["student_id"]) for record in records],
    )

    existing_rows = session.exec(
        select(Attendance).where(
            Attendance.class_id == class_id,
            Attendance.session_date == session_date,
            Attendance.student_id.in_(unique_student_ids),
        )
    ).all()
    existing_by_student = {row.student_id: row for row in existing_rows}

    missing_student_ids = [student_id for student_id in unique_student_ids if student_id not in existing_by_student]
    if missing_student_ids:
        raise AppError(
            "ATTENDANCE_RECORDS_NOT_FOUND",
            f"Attendance records not found for session_date {session_date}: {missing_student_ids}",
            404,
        )

    for record in records:
        student_id = int(record["student_id"])
        present = bool(record["present"])

        row = existing_by_student[student_id]
        row.present = present
        session.add(row)

    session.commit()

    return get_attendance_records(
        session=session,
        teacher_payload=teacher_payload,
        class_id=class_id,
        session_date=session_date,
    )
