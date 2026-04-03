from fastapi import FastAPI, Request, Depends ,HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from backend.config import AGENT_HOST, AGENT_PORT
from backend.models import ApiMessage


app = FastAPI(
    title="Digi-School AI Agent Server",
    version="1.0.0",
    description="Multi-agent backend for the Digi-School AI platform",
)

# ─── Health check ────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "server": "Digi-School Agent Server"}


# ─── Main agent endpoint ─────────────────────

security = HTTPBearer()

# 2. POST endpoint (receives from Node)
@app.post("/agent/run")
async def run_agent(
    data: ApiMessage,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        if not data.message:
            raise HTTPException(status_code=400, detail="No message provided")

        token = credentials.credentials


        # 3. YOUR LOGIC HERE (LLM, DB, etc.)
        result = agent(token, data)
        #!!!agent should return in a pydantic object type ApiMessage
        # and its to be changed to the real run agent function that will be implemented

        # 4. SEND response back to Node
        return result  # Fastapi will convert pydantic object to JSON automatically instead of dump_json
    except Exception as e:
        return {"reply": "server error", "error": str(e)}


# ─── Global error handler (in case) ────────────────────

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