from fastapi import APIRouter, Depends, Query, Path, HTTPException, Body
from sqlmodel import Session
from pydantic import BaseModel, Field
from typing import Any, AsyncIterator, Dict, List


from backend.server.db.engine import get_session
from backend.server.auth.jwt import verify_token
from backend.server.auth.dependencies import require_auth  # 🔑 Your dependency
from backend.flags.main import (
    create_flag_service,
    get_flags_service,
    delete_flag_service
)

router = APIRouter(prefix="/flags", tags=["Student Flags"])

# ─── SCHEMAS ──────────────────────────────────────────────────────────────────
class CreateFlagRequest(BaseModel):
    class_id: int
    student_id: int
    reason: str = Field(..., max_length=500)


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────
@router.post("", status_code=201)
def create_flag(payload: CreateFlagRequest,
                teacher: Dict[str, Any] = Depends(require_auth),
                session: Session = Depends(get_session)):
    try:
        return create_flag_service(session, teacher["id"], payload.class_id, payload.student_id, payload.reason)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to create flag: {str(e)}")


@router.get("")
def get_flags(
    session: Session = Depends(get_session),
    teacher : Dict[str, Any] = Depends(require_auth),
    class_id: int = Query(...),
    student_id: int = Query(...),
):
    try:
        return get_flags_service(session, teacher["id"], class_id, student_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch flags: {str(e)}")


@router.delete("/{flag_id}")
def delete_flag(
    flag_id: int = Path(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    try:
        return delete_flag_service(session, teacher["id"], flag_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete flag: {str(e)}")