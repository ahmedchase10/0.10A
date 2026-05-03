from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from typing import Any, Dict
from backend.server.auth.dependencies import require_auth
from backend.attendance.main import _get_owned_class_or_404,_validate_enrolled_students

from backend.server.db.engine import get_session
from backend.agents.email_agent.agent import generate_email_service

router = APIRouter(prefix="/emailagent", tags=["AI Email Agent"])

class GenerateEmailRequest(BaseModel):
    custom: bool
    teacher_prompt: str
    class_id: int
    student_id: Optional[int] = None
    selected_flags: Optional[List[int]] = None  # Flag IDs to include
    recipient_email: Optional[str] = None
@router.post("/generate-email")
def generate_email_endpoint(
    payload: GenerateEmailRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    # 🔍 Validation based on mode
    _get_owned_class_or_404(session, teacher_id=teacher["id"], class_id=payload.class_id)
    _validate_enrolled_students(session, class_id=payload.class_id, student_ids=[payload.student_id] if payload.student_id else [])
    if not payload.custom and not payload.student_id:
        raise HTTPException(400, "student_id is required when custom=false")
    if payload.custom and not payload.recipient_email:
        raise HTTPException(400, "recipient_email is required when custom=true")

    try:
        result = generate_email_service(
            session=session,
            custom=payload.custom,
            teacher_prompt=payload.teacher_prompt,
            student_id=payload.student_id,
            selected_flags=payload.selected_flags,
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))