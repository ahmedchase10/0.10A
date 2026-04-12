from typing import Dict, Any

from fastapi import APIRouter, Depends

from backend.server.auth.dependencies import require_auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def get_me(teacher: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    return {
        "success": True,
        "teacher": {
            "id": teacher["id"],
            "name": teacher["name"],
            "email": teacher["email"],
        },
    }

