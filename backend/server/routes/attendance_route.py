from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session

from backend.attendance.main import (
	create_attendance_records,
	get_attendance_records,
	update_attendance_presence,
)
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/attendance", tags=["attendance"])


class AttendanceRecord(BaseModel):
	student_id: int
	present: bool


class CreateAttendanceRequest(BaseModel):
	class_id: int
	session_date: date
	records: List[AttendanceRecord]


@router.post("")
def create_attendance_route(
	payload: CreateAttendanceRequest,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return create_attendance_records(
		session=session,
		teacher_payload=teacher,
		class_id=payload.class_id,
		session_date=payload.session_date,
		records=[record.model_dump() for record in payload.records],
	)


@router.get("")
def get_attendance_route(
	class_id: int = Query(...),
	session_date: date = Query(...),
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return get_attendance_records(
		session=session,
		teacher_payload=teacher,
		class_id=class_id,
		session_date=session_date,
	)


@router.put("")
def update_attendance_route(
	payload: CreateAttendanceRequest,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return update_attendance_presence(
		session=session,
		teacher_payload=teacher,
		class_id=payload.class_id,
		session_date=payload.session_date,
		records=[record.model_dump() for record in payload.records],
	)
