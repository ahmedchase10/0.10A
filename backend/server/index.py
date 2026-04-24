from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.models import AppError
from backend.server.auth.me import router as auth_router
from backend.server.routes.teacher_route import router as login_router, teachers_router
from backend.server.routes.lessons_route import router as lessons_router
from backend.server.routes.classes_route import router as classes_router
from backend.server.routes.students_route import router as students_router
from backend.server.routes.attendance_route import router as attendance_router
from backend.server.routes.timetable_route import router as timetable_router
from backend.server.routes.exam_types_route import router as exam_types_router
from backend.server.routes.grades_route import router as grades_router
from backend.server.routes.agents_route import router as agents_router
from backend.server.routes.grading_route import router as grading_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    from backend.agents.db import get_checkpointer
    await get_checkpointer()   # opens shared pool + creates checkpoint tables once for all agents
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    from backend.agents.db import close_pool
    await close_pool()


app = FastAPI(title="Digi-School API", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else None
    msg = first.get("msg") if first else "Invalid request data."
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg,
            },
        },
    )

@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException):
    status_to_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
    }
    error_code = status_to_code.get(exc.status_code, "HTTP_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": str(exc.detail),
            },
        },
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Something went wrong.",
            },
        },
    )

@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )



@app.get("/health")
def health_check():
    return {"success": True, "status": "ok"}


app.include_router(auth_router)
app.include_router(login_router)
app.include_router(teachers_router)
app.include_router(lessons_router)
app.include_router(classes_router)
app.include_router(students_router)
app.include_router(attendance_router)
app.include_router(timetable_router)
app.include_router(exam_types_router)
app.include_router(grades_router)
app.include_router(agents_router)
app.include_router(grading_router)
