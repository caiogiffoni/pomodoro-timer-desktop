import json
from datetime import date
from pathlib import Path

_STATS_FILE = Path.home() / ".config" / "pomodoro" / "stats.json"


def _load() -> dict:
    if not _STATS_FILE.exists():
        return {}
    try:
        return json.loads(_STATS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATS_FILE.write_text(json.dumps(data, indent=2))


def record_session() -> None:
    data = _load()
    key = date.today().isoformat()
    data[key] = data.get(key, 0) + 1
    _save(data)


def today_count() -> int:
    data = _load()
    return data.get(date.today().isoformat(), 0)


def all_time_count() -> int:
    return sum(_load().values())


def last_7_days(week_offset: int = 0) -> list[tuple[str, int]]:
    from datetime import timedelta
    data = _load()
    end = date.today() - timedelta(weeks=week_offset)
    return [
        ((end - timedelta(days=i)).strftime("%a"), data.get((end - timedelta(days=i)).isoformat(), 0))
        for i in range(6, -1, -1)
    ]


def all_days() -> list[tuple[str, int]]:
    return sorted(_load().items(), reverse=True)
