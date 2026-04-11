from typing import Dict, Any

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.models import AppError
from backend.server.auth.jwt import verify_token

_bearer = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """Validate Bearer token and return decoded teacher payload."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="AUTH_MISSING_TOKEN",
            message="Access denied. No token provided.",
            status_code=401,
        )

    try:
        return verify_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise AppError(
            code="AUTH_INVALID_TOKEN",
            message="Invalid or expired token.",
            status_code=401,
        )
