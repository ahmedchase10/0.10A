from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError


def ensure_student_parent_email_column(engine: Engine) -> None:
    """Add the parent_email column for older databases that predate the schema change."""
    inspector = inspect(engine)

    try:
        columns = {column["name"] for column in inspector.get_columns("students")}
    except NoSuchTableError:
        return

    if "parent_email" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE students ADD COLUMN parent_email VARCHAR(150)"))
