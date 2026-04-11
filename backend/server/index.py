from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.models import AppError
from backend.server.auth.me import router as auth_router
from backend.server.routes.login_route import router as login_router

app = FastAPI(title="Digi-School API")


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
