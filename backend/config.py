from dotenv import load_dotenv
import os

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5vl:3b"  # ← removed duplicate, keep vision model only

# ── ColQwen ───────────────────────────────────────────────────────────────
COLQWEN_MODEL = "athrael-soju/colqwen3.5-4.5B-v3"
PAGES_STORAGE_PATH = "./storage/pages"

# ── Weaviate ──────────────────────────────────────────────────────────────
WEAVIATE_PERSISTENCE_PATH = "./.collections"  # ← removed WEAVIATE_URL, using embedded
WEAVIATE_COLLECTION = "CoursePage"
WEAVIATE_VERSION = "1.31.0"  # ← add this, needed for connect_to_embedded

# ── PostgreSQL ────────────────────────────────────────────────────────────
#POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:password@localhost:5432/teacher_agent")

# ── Google APIs ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", os.path.join(BASE_DIR, "client_secret.json"))
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
CLASSROOM_SCOPES = ["https://www.googleapis.com/auth/classroom.courses"]

# ── RAG ───────────────────────────────────────────────────────────────────
TOP_K_RETRIEVAL = 5
TOP_K_RERANK = 3  # ← keep for now even though we removed reranking, might use later

JWS_AI_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwibmFtZSI6ImFkbWluIiwiZW1haWwiOiJhZG1pbjEyM0BzY2hvb2wudG4iLCJpYXQiOjE3NzQ4MjQ2MTgsImV4cCI6MTc3NTQyOTQxOH0.s4YT8nJg7o5Rh66ZO-8M_lyJZvvJgaZ46Naz6Kz3xiU"

# ─── PostgreSQL ───────────────────────────────

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "user":     os.getenv("DB_USER",     "digischool"),
    "password": os.getenv("DB_PASSWORD", "digischool123"),
    "dbname":   os.getenv("DB_NAME",     "digischool"),
}

# ─── Ollama ───────────────────────────────────

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.1:8b")

# ─── Agent server ─────────────────────────────

AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8000"))

# ─── Express API (for tools to call back) ─────

EXPRESS_API_URL = os.getenv("EXPRESS_API_URL", "http://localhost:3001/api")