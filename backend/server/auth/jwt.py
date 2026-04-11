from datetime import datetime, timedelta, timezone
import os
from typing import Dict, Any

import jwt
from dotenv import load_dotenv

load_dotenv()

_JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_TOKEN_TTL_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

if not _JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing in .env")


def create_token(teacher: Dict[str, Any]) -> str:
    """Create a token with the stable payload only."""
    now_utc = datetime.now(timezone.utc)
    payload = {
        "id": teacher["id"],
        "name": teacher["name"],
        "email": teacher["email"],
        "exp": now_utc + timedelta(days=_TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify signature/expiry and return the decoded payload."""
    decoded = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    return {
        "id": decoded["id"],
        "name": decoded["name"],
        "email": decoded["email"],
        "exp": decoded["exp"],
    }


__all__ = ["create_token", "verify_token"]

