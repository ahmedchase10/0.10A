# Frontend API Contract (FastAPI)

Base URL (local): `http://127.0.0.1:8000`

## Auth
Use Bearer token for protected endpoints:
`Authorization: Bearer <token>`

Unified error shape:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

---

## 1) Auth Endpoints

### `POST /auth/register`
Body (JSON):
```json
{
  "name": "Dusty",
  "email": "dusty@example.com",
  "password": "password123",
  "initials": "DS"
}
```
Success:
```json
{
  "success": true,
  "token": "<jwt>",
  "teacher": {
    "id": 1,
    "name": "Dusty",
    "email": "dusty@example.com"
  }
}
```

### `POST /auth/login`
Body (JSON):
```json
{
  "email": "dusty@example.com",
  "password": "password123"
}
```
Success shape: same as `/auth/register`.

### `GET /auth/me` (protected)
Success:
```json
{
  "success": true,
  "teacher": {
    "id": 1,
    "name": "Dusty",
    "email": "dusty@example.com"
  }
}
```

---

## 2) Classes Endpoints (protected)

### `GET /classes`
Returns classes for the logged-in teacher.

Success:
```json
{
  "success": true,
  "classes": [
    {
      "id": 1,
      "name": "3eme Info",
      "subject": "Math",
      "teacher_id": 1,
      "created_at": "2026-04-12T10:00:00Z"
    }
  ]
}
```

### `POST /classes`
Body (JSON):
```json
{
  "name": "3eme Info",
  "subject": "Math"
}
```
Success:
```json
{
  "success": true,
  "class": {
    "id": 1,
    "name": "3eme Info",
    "subject": "Math",
    "teacher_id": 1,
    "created_at": "2026-04-12T10:00:00Z"
  }
}
```

Class-specific error codes:
- `CLASSES_INVALID_NAME`
- `CLASSES_INVALID_SUBJECT`
- `CLASSES_ALREADY_EXISTS`

---

## 3) Lessons Endpoints (protected)

### `POST /lessons/upload`
Content type: `multipart/form-data`

Fields:
- `file` (PDF)
- `class_id` (integer)

Success:
```json
{
  "success": true,
  "upload": {
    "id": "uuid",
    "name": "lesson.pdf",
    "size": 123456,
    "created_at": "2026-04-12T10:00:00Z",
    "already_exists": false
  }
}
```

### `GET /lessons`
Query params:
- `class_id` (required, int)
- `limit` (optional, default `20`, min `1`, max `100`)
- `offset` (optional, default `0`, min `0`)
- `sort` (optional, default `created_at_desc`)
- `refresh` (optional, default `true`)

Allowed `sort` values:
- `created_at_desc`
- `created_at_asc`
- `name_asc`
- `name_desc`
- `size_asc`
- `size_desc`

Success:
```json
{
  "success": true,
  "uploads": [
    {
      "id": "uuid",
      "name": "lesson.pdf",
      "size": 123456,
      "created_at": "2026-04-12T10:00:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "sort": "created_at_desc"
  }
}
```

Lessons-specific error codes:
- `LESSONS_CLASS_NOT_FOUND`
- `LESSONS_CLASS_FORBIDDEN`
- `LESSONS_INVALID_PAGINATION`
- `LESSONS_INVALID_SORT`
- `LESSONS_INVALID_FILE_TYPE`
- `LESSONS_FILE_TOO_LARGE`
- `LESSONS_MISSING_FILENAME`

---

## 4) Generic Error Codes
These may also appear depending on validation/exceptions:
- `VALIDATION_ERROR` (422)
- `BAD_REQUEST` (400)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `CONFLICT` (409)
- `PAYLOAD_TOO_LARGE` (413)
- `INTERNAL_SERVER_ERROR` (500)

---

## Frontend Notes
- Save JWT from login/register and attach on every protected request.
- Always select/create class first, then pass `class_id` for lessons endpoints.
- For lessons page refresh, call `GET /lessons` with `refresh=true`.

