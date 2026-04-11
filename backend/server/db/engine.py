from typing import Generator
import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Set it in .env, for example: "
        "postgresql+psycopg://user:password@localhost:5432/dbname"
    )
engine = create_engine(DATABASE_URL, echo=False)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yields one SQLModel session per request."""
    with Session(engine) as session:
        yield session

