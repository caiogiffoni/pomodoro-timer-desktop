import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_DB_PATH = Path.home() / ".config" / "pomodoro" / "pomodoro.db"
_STATS_JSON = Path.home() / ".config" / "pomodoro" / "stats.json"
_STATS_BAK = Path.home() / ".config" / "pomodoro" / "stats.json.bak"

_pending_session_id: int | None = None


@contextmanager
def _db():
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                date                     TEXT NOT NULL,
                started_at               TEXT NOT NULL,
                completed_at             TEXT,
                planned_duration_seconds INTEGER,
                pomodoro_number          INTEGER,
                day_session_index        INTEGER,
                notes                    TEXT,
                tag                      TEXT,
                focus_score              INTEGER
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date)"
        )
        # Add columns to pre-existing DBs that only have the original 4 columns
        existing = {row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        for col, col_type in [
            ("planned_duration_seconds", "INTEGER"),
            ("pomodoro_number", "INTEGER"),
            ("day_session_index", "INTEGER"),
            ("notes", "TEXT"),
            ("tag", "TEXT"),
            ("focus_score", "INTEGER"),
        ]:
            if col not in existing:
                conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_type}")
    _migrate_from_json()


def _migrate_from_json() -> None:
    if not _STATS_JSON.exists() or _STATS_BAK.exists():
        return
    try:
        data: dict = json.loads(_STATS_JSON.read_text())
    except (json.JSONDecodeError, OSError):
        return
    with _db() as conn:
        for date_str, count in data.items():
            placeholder = f"{date_str}T00:00:00"
            for _ in range(count):
                conn.execute(
                    "INSERT INTO sessions (date, started_at, completed_at) VALUES (?, ?, ?)",
                    (date_str, placeholder, placeholder),
                )
    _STATS_JSON.rename(_STATS_BAK)


def begin_session(planned_duration_seconds: int, pomodoro_number: int) -> None:
    global _pending_session_id
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with _db() as conn:
        day_idx = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date = ? AND completed_at IS NOT NULL",
            (today,),
        ).fetchone()[0] + 1
        cur = conn.execute(
            "INSERT INTO sessions"
            " (date, started_at, planned_duration_seconds, pomodoro_number, day_session_index)"
            " VALUES (?, ?, ?, ?, ?)",
            (today, now, planned_duration_seconds, pomodoro_number, day_idx),
        )
        _pending_session_id = cur.lastrowid


def record_session() -> int | None:
    global _pending_session_id
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with _db() as conn:
        if _pending_session_id is not None:
            session_id = _pending_session_id
            conn.execute(
                "UPDATE sessions SET completed_at = ? WHERE id = ?",
                (now, session_id),
            )
            _pending_session_id = None
        else:
            today = date.today().isoformat()
            cur = conn.execute(
                "INSERT INTO sessions (date, started_at, completed_at) VALUES (?, ?, ?)",
                (today, now, now),
            )
            session_id = cur.lastrowid
    return session_id


def update_session(
    session_id: int,
    notes: str | None,
    tag: str | None,
    focus_score: int | None,
) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE sessions SET notes = ?, tag = ?, focus_score = ? WHERE id = ?",
            (notes, tag, focus_score, session_id),
        )


def last_review_today(exclude_id: int) -> tuple[str | None, str | None, int | None]:
    """Return (notes, tag, focus_score) from the most recent completed session today, excluding the given id."""
    with _db() as conn:
        row = conn.execute(
            "SELECT notes, tag, focus_score FROM sessions"
            " WHERE date = ? AND completed_at IS NOT NULL AND id != ?"
            " ORDER BY completed_at DESC LIMIT 1",
            (date.today().isoformat(), exclude_id),
        ).fetchone()
    if row is None:
        return (None, None, None)
    return (row[0], row[1], row[2])


def today_count() -> int:
    with _db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date = ? AND completed_at IS NOT NULL",
            (date.today().isoformat(),),
        ).fetchone()[0]


def all_time_count() -> int:
    with _db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE completed_at IS NOT NULL"
        ).fetchone()[0]


def last_7_days(week_offset: int = 0) -> list[tuple[str, int]]:
    end = date.today() - timedelta(weeks=week_offset)
    days = [end - timedelta(days=i) for i in range(6, -1, -1)]
    placeholders = ",".join("?" * 7)
    with _db() as conn:
        rows = conn.execute(
            f"SELECT date, COUNT(*) FROM sessions"
            f" WHERE date IN ({placeholders}) AND completed_at IS NOT NULL"
            f" GROUP BY date",
            [d.isoformat() for d in days],
        ).fetchall()
    counts = {row[0]: row[1] for row in rows}
    return [(d.strftime("%a"), counts.get(d.isoformat(), 0)) for d in days]


def all_days() -> list[tuple[str, int]]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT date, COUNT(*) FROM sessions"
            " WHERE completed_at IS NOT NULL"
            " GROUP BY date ORDER BY date DESC"
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def streak() -> int:
    today_iso = date.today().isoformat()
    with _db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date = ? AND completed_at IS NOT NULL",
            (today_iso,),
        ).fetchone()[0]
        d = date.today() if n else date.today() - timedelta(days=1)
        count = 0
        while True:
            n = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE date = ? AND completed_at IS NOT NULL",
                (d.isoformat(),),
            ).fetchone()[0]
            if not n:
                break
            count += 1
            d -= timedelta(days=1)
    return count
