import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "bugpilot.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id          TEXT PRIMARY KEY,
                issue_key   TEXT NOT NULL,
                summary     TEXT DEFAULT '',
                status      TEXT DEFAULT 'PENDING',
                stage       TEXT DEFAULT '',
                pr_url      TEXT DEFAULT '',
                error       TEXT DEFAULT '',
                retry_count INTEGER DEFAULT 0,
                created_at  REAL,
                updated_at  REAL
            )
        """)
        conn.commit()


def create_run(run_id: str, issue_key: str, summary: str = ""):
    now = time.time()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO runs (id, issue_key, summary, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'PENDING', ?, ?)",
            (run_id, issue_key, summary, now, now),
        )
        conn.commit()


def update_run(run_id: str, **kwargs):
    kwargs["updated_at"] = time.time()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [run_id]
    with get_db() as conn:
        conn.execute(f"UPDATE runs SET {sets} WHERE id = ?", vals)
        conn.commit()


def get_run(run_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else None


def list_runs() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
