"""
RevFlow Database Connection — SQLite with foreign keys enabled.

Per §3: SQLite database with seven tables. Foreign keys must be enforced.
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

from revflow.contracts.config import DATABASE_PATH


def get_project_root() -> str:
    """Get the project root directory (containing backend/, frontend/, docs/)."""
    # Start from this file's directory and go up to find project root
    current = os.path.dirname(os.path.abspath(__file__))
    while current and not os.path.exists(os.path.join(current, "docs", "00_CONTRACTS_RevFlow.md")):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current


def get_db_path() -> str:
    """Get database path from environment or config default, resolved relative to project root."""
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        # If absolute, use as-is; if relative, resolve from project root
        if os.path.isabs(env_path):
            return env_path
        return os.path.join(get_project_root(), env_path)
    # Default from config - resolve relative to project root
    if os.path.isabs(DATABASE_PATH):
        return DATABASE_PATH
    return os.path.join(get_project_root(), DATABASE_PATH)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Get a database connection with foreign keys enabled.
    Connection is automatically committed/rolled back and closed.
    """
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints (required per §3)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the database by running schema.sql.
    Creates all seven tables per §3 if they don't exist.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    with get_connection() as conn:
        conn.executescript(schema_sql)


def reset_db() -> None:
    """Drop all tables and reinitialize. Used for testing (NFR-8)."""
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()