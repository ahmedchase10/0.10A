from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from backend.timetable.main import bulk_upsert_timetable_entries, delete_timetable_entry, get_teacher_timetable
from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session

router = APIRouter(prefix="/timetable", tags=["timetable"])


class TimetableEntry(BaseModel):
	class_id: int
	day_of_week: int = Field(ge=0, le=6, description="0 = Monday, 6 = Sunday")
	start_time: str = Field(pattern=r'^([01][0-9]|2[0-3]):([0-5][0-9])$', description="HH:MM")
	end_time: str = Field(pattern=r'^([01][0-9]|2[0-3]):([0-5][0-9])$', description="HH:MM")
	classroom: Optional[str] = None


class BulkUpsertTimetableRequest(BaseModel):
	entries: List[TimetableEntry]


@router.get("")
def get_timetable_route(
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return get_teacher_timetable(
		session=session,
		teacher_payload=teacher,
	)


@router.post("")
def bulk_upsert_timetable_route(
	payload: BulkUpsertTimetableRequest,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return bulk_upsert_timetable_entries(
		session=session,
		teacher_payload=teacher,
		entries=[entry.model_dump() for entry in payload.entries],
	)


@router.delete("/{timetable_id}")
def delete_timetable_route(
	timetable_id: int,
	teacher: Dict[str, Any] = Depends(require_auth),
	session: Session = Depends(get_session),
):
	return delete_timetable_entry(
		session=session,
		teacher_payload=teacher,
		timetable_id=timetable_id,
	)
