# FastAPI Auth Core

This folder owns JWT auth for the FastAPI server.

## Files
- `jwt.py`: only `create_token(...)` and `verify_token(...)`.
- `dependencies.py`: `require_auth` FastAPI dependency and auth error type.
- `me.py`: `/auth/me` route used to validate token flow.

## Token contract
Payload is fixed and minimal:
- `id`
- `name`
- `email`
- `exp` (UTC)

## Required env vars
- `JWT_SECRET`
- `JWT_ALGORITHM` (default `HS256`)
- `JWT_EXPIRE_DAYS` (default `7`)

## Unified 401 response
```json
{
  "success": false,
  "error": {
    "code": "AUTH_MISSING_TOKEN",
    "message": "Access denied. No token provided."
  }
}
```

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Invalid or expired token."
  }
}
```

