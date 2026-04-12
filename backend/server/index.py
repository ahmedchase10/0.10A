from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.models import AppError
from backend.server.auth.me import router as auth_router
from backend.server.routes.login_route import router as login_router
from backend.server.routes.lessons_route import router as lessons_router
from backend.server.routes.classes_route import router as classes_router
app = FastAPI(title="Digi-School API")


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
app.include_router(lessons_router)
app.include_router(classes_router)
