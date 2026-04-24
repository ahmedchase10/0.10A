"""
backend/agents/db.py
--------------------
Shared AsyncConnectionPool + AsyncPostgresSaver for ALL agents.

Both the pedagogical agent and the grading agent call get_checkpointer()
to obtain the same pool, avoiding multiple Postgres connection pools.
close_pool() is called once in the FastAPI lifespan shutdown.
"""
import sys

# Windows: psycopg3 async requires SelectorEventLoop
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.config import POSTGRES_URL

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None


def _psycopg_url(url: str) -> str:
    """Strip SQLAlchemy driver prefix so psycopg3 can use it directly."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Lazily open the pool and return the shared checkpointer.
    Safe to call multiple times — initialises only once.

    Pool kwargs MUST include:
      autocommit=True  — required by AsyncPostgresSaver for all operations
      row_factory=dict_row — rows returned as dicts, not tuples
    """
    global _pool, _checkpointer
    if _checkpointer is None:
        _pool = AsyncConnectionPool(
            conninfo=_psycopg_url(POSTGRES_URL),
            max_size=10,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
            },
            open=False,
        )
        await _pool.open()
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()   # creates checkpoint_* tables if not present
    return _checkpointer


async def close_pool() -> None:
    """Close the pool cleanly on app shutdown."""
    global _pool, _checkpointer
    if _pool is not None:
        await _pool.close()
        _pool = None
        _checkpointer = None


async def delete_thread(thread_id: str) -> None:
    """
    Hard-delete all LangGraph checkpoint data for a given thread_id.
    Used when soft-deleting a blueprint or force-restarting a grading session.
    """
    await get_checkpointer()  # ensure pool is open
    async with _pool.connection() as conn:  # type: ignore[union-attr]
        for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
            await conn.execute(  # type: ignore[arg-type]
                f"DELETE FROM {table} WHERE thread_id = $1",
                (thread_id,),
            )


async def fork_thread(source_thread_id: str, dest_thread_id: str) -> None:
    """
    Copy all LangGraph checkpoint data from source_thread_id → dest_thread_id.

    This is the blueprint → student fork:
    The blueprint thread's full suspended state (all messages, exam page images,
    RAG results, agent analysis) is copied to a new thread. Each student grading
    session resumes from this fork — the agent already knows the exam and needs
    only to read that one student's paper.

    Uses ON CONFLICT DO NOTHING so repeated calls are safe (idempotent).
    """
    await get_checkpointer()  # ensure pool is open
    async with _pool.connection() as conn:  # type: ignore[union-attr]
        # checkpoint_blobs before checkpoints (foreign-key dependency order)
        await conn.execute(  # type: ignore[arg-type]
            """
            INSERT INTO checkpoint_blobs
                (thread_id, checkpoint_ns, channel, version, type, blob)
            SELECT $2, checkpoint_ns, channel, version, type, blob
            FROM checkpoint_blobs WHERE thread_id = $1
            ON CONFLICT DO NOTHING
            """,
            (source_thread_id, dest_thread_id),
        )
        await conn.execute(  # type: ignore[arg-type]
            """
            INSERT INTO checkpoints
                (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                 type, checkpoint, metadata)
            SELECT $2, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                   type, checkpoint, metadata
            FROM checkpoints WHERE thread_id = $1
            ON CONFLICT DO NOTHING
            """,
            (source_thread_id, dest_thread_id),
        )
        await conn.execute(  # type: ignore[arg-type]
            """
            INSERT INTO checkpoint_writes
                (thread_id, checkpoint_ns, checkpoint_id, task_id, idx,
                 channel, type, blob, task_path)
            SELECT $2, checkpoint_ns, checkpoint_id, task_id, idx,
                   channel, type, blob, task_path
            FROM checkpoint_writes WHERE thread_id = $1
            ON CONFLICT DO NOTHING
            """,
            (source_thread_id, dest_thread_id),
        )


