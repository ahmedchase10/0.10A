# =============================================
# DIGI-SCHOOL AI — FastAPI Agent Server
# Port: 8000
# Start: uvicorn backend.main:app --reload
# =============================================

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.config import AGENT_HOST, AGENT_PORT
from backend.models import AgentRequest, AgentResponse


app = FastAPI(
    title="Digi-School AI Agent Server",
    version="1.0.0",
    description="Multi-agent backend for the Digi-School AI platform",
)

# ─── CORS ────────────────────────────────────
# Allow requests from Node.js server and Vite frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",   # Node.js API
        "http://localhost:5173",   # Vite frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health check ────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "server": "Digi-School Agent Server"}


# ─── Main agent endpoint ─────────────────────
# Called by Node.js POST /api/ai/agent → POST /agent/run

@app.post("/agent/run", response_model=AgentResponse)
async def run_agent(
    request:       AgentRequest,
    authorization: str = Header(default=""),
):
    """
    Receives teacher input + context from Node.js.
    Routes to the correct agent based on input classification.
    Returns structured actions + summary.
    """
    # Extract JWT token (forwarded from frontend through Node.js)
    jwt_token = authorization.replace("Bearer ", "").strip()

    # For now, all inputs go to the attendance agent.
    # The orchestrator will handle routing later.
    from backend.agents.attendance_agent import run_attendance_agent

    try:
        response = await run_attendance_agent(request, jwt_token)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Per-agent endpoints (for direct testing) ─

@app.post("/agent/attendance", response_model=AgentResponse)
async def run_attendance(
    request:       AgentRequest,
    authorization: str = Header(default=""),
):
    """Direct endpoint to test the attendance agent only."""
    from backend.agents.attendance_agent import run_attendance_agent
    jwt_token = authorization.replace("Bearer ", "").strip()
    try:
        return await run_attendance_agent(request, jwt_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Global error handler ────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ─── Entry point ─────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=AGENT_HOST,
        port=AGENT_PORT,
        reload=True,
    )