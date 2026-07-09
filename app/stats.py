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
                focus_score              INTEGER,
                project_id               INTEGER REFERENCES projects(id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                archived   INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Add columns to pre-existing DBs that only have the original 4 columns
        existing = {row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        for col, col_type in [
            ("planned_duration_seconds", "INTEGER"),
            ("pomodoro_number", "INTEGER"),
            ("day_session_index", "INTEGER"),
            ("notes", "TEXT"),
            ("tag", "TEXT"),
            ("focus_score", "INTEGER"),
            ("project_id", "INTEGER REFERENCES projects(id)"),
        ]:
            if col not in existing:
                conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_type}")
        # Backfill: DBs from the short-lived free-text era have a `project` TEXT column
        if "project" in existing:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            names = conn.execute(
                "SELECT DISTINCT project FROM sessions"
                " WHERE project IS NOT NULL AND project != ''"
            ).fetchall()
            for (name,) in names:
                row = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
                pid = row[0] if row else conn.execute(
                    "INSERT INTO projects (name, created_at) VALUES (?, ?)", (name, now)
                ).lastrowid
                conn.execute(
                    "UPDATE sessions SET project_id = ? WHERE project = ? AND project_id IS NULL",
                    (pid, name),
                )
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


def begin_session(
    planned_duration_seconds: int,
    pomodoro_number: int,
    project_id: int | None = None,
) -> None:
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
            " (date, started_at, planned_duration_seconds, pomodoro_number, day_session_index, project_id)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (today, now, planned_duration_seconds, pomodoro_number, day_idx, project_id),
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
    project_id: int | None = None,
) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE sessions SET notes = ?, tag = ?, focus_score = ?, project_id = ?"
            " WHERE id = ?",
            (notes, tag, focus_score, project_id, session_id),
        )


def last_review_today(
    exclude_id: int,
) -> tuple[str | None, str | None, int | None, int | None]:
    """Return (notes, tag, focus_score, project_id) from the most recent completed session today, excluding the given id."""
    with _db() as conn:
        row = conn.execute(
            "SELECT notes, tag, focus_score, project_id FROM sessions"
            " WHERE date = ? AND completed_at IS NOT NULL AND id != ?"
            " ORDER BY completed_at DESC, id DESC LIMIT 1",
            (date.today().isoformat(), exclude_id),
        ).fetchone()
    if row is None:
        return (None, None, None, None)
    return (row[0], row[1], row[2], row[3])


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


def _since_clause(days: int | None) -> tuple[str, list]:
    """SQL fragment + params restricting to the last N days (None = all time)."""
    if days is None:
        return "", []
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    return " AND date >= ?", [start]


def dashboard_summary(days: int | None = None) -> dict:
    """Aggregate stats over completed sessions in the period.

    Focus time uses planned_duration_seconds, falling back to the
    started→completed delta for rows that predate that column.
    """
    clause, params = _since_clause(days)
    with _db() as conn:
        row = conn.execute(
            "SELECT COUNT(*),"
            " COALESCE(SUM(COALESCE(planned_duration_seconds,"
            "   MAX((julianday(completed_at) - julianday(started_at)) * 86400, 0))), 0),"
            " AVG(focus_score),"
            " COUNT(DISTINCT date)"
            f" FROM sessions WHERE completed_at IS NOT NULL{clause}",
            params,
        ).fetchone()
    return {
        "sessions": row[0],
        "focus_seconds": int(row[1]),
        "avg_focus": row[2],
        "active_days": row[3],
    }


def _breakdown(column: str, days: int | None, limit: int) -> list[tuple[str, int]]:
    clause, params = _since_clause(days)
    with _db() as conn:
        rows = conn.execute(
            f"SELECT {column}, COUNT(*) FROM sessions"
            f" WHERE completed_at IS NOT NULL AND {column} IS NOT NULL AND {column} != ''{clause}"
            f" GROUP BY {column} ORDER BY COUNT(*) DESC, {column} LIMIT ?",
            params + [limit],
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def tag_breakdown(days: int | None = None, limit: int = 5) -> list[tuple[str, int]]:
    return _breakdown("tag", days, limit)


def project_breakdown(days: int | None = None, limit: int = 5) -> list[tuple[str, int]]:
    """Completed sessions per project (archived projects included — history is kept)."""
    clause, params = _since_clause(days)
    with _db() as conn:
        rows = conn.execute(
            "SELECT p.name, COUNT(*) FROM sessions s"
            " JOIN projects p ON p.id = s.project_id"
            f" WHERE s.completed_at IS NOT NULL{clause}"
            " GROUP BY p.id ORDER BY COUNT(*) DESC, p.name LIMIT ?",
            params + [limit],
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def ensure_project(name: str) -> int:
    """Return the id for a project name, creating (or un-archiving) it if needed."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with _db() as conn:
        row = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
        if row is not None:
            conn.execute("UPDATE projects SET archived = 0 WHERE id = ?", (row[0],))
            return row[0]
        cur = conn.execute(
            "INSERT INTO projects (name, created_at) VALUES (?, ?)", (name, now)
        )
        return cur.lastrowid


def list_projects() -> list[tuple[int, str, int]]:
    """Active (non-archived) projects as (id, name, completed_session_count)."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT p.id, p.name,"
            " (SELECT COUNT(*) FROM sessions s"
            "   WHERE s.project_id = p.id AND s.completed_at IS NOT NULL)"
            " FROM projects p WHERE p.archived = 0 ORDER BY p.id"
        ).fetchall()
    return [(row[0], row[1], row[2]) for row in rows]


def archive_project(project_id: int) -> None:
    """Hide a project from the list; its sessions keep their link for history."""
    with _db() as conn:
        conn.execute("UPDATE projects SET archived = 1 WHERE id = ?", (project_id,))


def project_name(project_id: int) -> str | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT name FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    return row[0] if row else None


def hour_histogram(days: int | None = None) -> list[int]:
    """Completed-session counts bucketed by local start hour (24 buckets)."""
    clause, params = _since_clause(days)
    with _db() as conn:
        rows = conn.execute(
            f"SELECT started_at FROM sessions WHERE completed_at IS NOT NULL{clause}",
            params,
        ).fetchall()
    counts = [0] * 24
    for (started_at,) in rows:
        try:
            dt = datetime.fromisoformat(started_at)
        except ValueError:
            continue
        local = dt.replace(tzinfo=timezone.utc).astimezone()
        counts[local.hour] += 1
    return counts


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
