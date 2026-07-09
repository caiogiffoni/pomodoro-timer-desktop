"""Dashboard tab: summary aggregates, tag breakdown, hour histogram, period filter."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

from PyQt6.QtGui import QIcon

from app import stats
from app.notifier import Notifier
from app.timer import PomodoroTimer
from app.window import MainWindow


def _record(planned=1500, tag=None, focus_score=None):
    stats.begin_session(planned_duration_seconds=planned, pomodoro_number=1)
    session_id = stats.record_session()
    if tag is not None or focus_score is not None:
        stats.update_session(session_id, notes=None, tag=tag, focus_score=focus_score)
    return session_id


def _insert_on(day: date, planned=1500, tag=None) -> None:
    ts = day.isoformat() + "T10:00:00"
    with stats._db() as conn:
        conn.execute(
            "INSERT INTO sessions"
            " (date, started_at, completed_at, planned_duration_seconds, tag)"
            " VALUES (?, ?, ?, ?, ?)",
            (day.isoformat(), ts, ts, planned, tag),
        )


def test_dashboard_summary_aggregates(tmp_config):
    _record(planned=1500, focus_score=4)
    _record(planned=1500, focus_score=2)
    _record(planned=600)

    s = stats.dashboard_summary(7)
    assert s["sessions"] == 3
    assert s["focus_seconds"] == 3600
    assert s["avg_focus"] == 3.0
    assert s["active_days"] == 1


def test_dashboard_summary_empty(tmp_config):
    s = stats.dashboard_summary(7)
    assert s == {"sessions": 0, "focus_seconds": 0, "avg_focus": None, "active_days": 0}


def test_summary_excludes_incomplete_sessions(tmp_config):
    stats.begin_session(planned_duration_seconds=1500, pomodoro_number=1)
    # never completed
    assert stats.dashboard_summary(None)["sessions"] == 0


def test_period_filter_excludes_old_sessions(tmp_config):
    _insert_on(date.today() - timedelta(days=40))
    _record()

    assert stats.dashboard_summary(30)["sessions"] == 1
    assert stats.dashboard_summary(None)["sessions"] == 2


def test_tag_breakdown_ordered_by_count(tmp_config):
    _record(tag="Coding")
    _record(tag="Coding")
    _record(tag="Reading")
    _record()  # untagged, excluded

    assert stats.tag_breakdown(7) == [("Coding", 2), ("Reading", 1)]


def test_hour_histogram_uses_local_hour(tmp_config):
    _record()
    now_utc = datetime.now(timezone.utc)
    expected_hour = now_utc.astimezone().hour

    counts = stats.hour_histogram(7)
    assert len(counts) == 24
    assert counts[expected_hour] == 1
    assert sum(counts) == 1


def test_dashboard_tab_reflects_db(qtbot, tmp_config):
    _record(tag="Coding", focus_score=5)
    _record(tag="Coding", focus_score=3)

    window = MainWindow(
        timer=PomodoroTimer(),
        icon=QIcon(),
        cfg=tmp_config,
        notifier=MagicMock(spec=Notifier),
    )
    qtbot.addWidget(window)
    window.show()
    window.centralWidget().setCurrentIndex(2)

    page = window._dashboard_page
    qtbot.waitUntil(lambda: page._val_sessions.text() == "2", timeout=1000)
    assert page._val_time.text() == "50m"
    assert page._val_focus.text() == "4.0 ★"
    assert page._tags._data == [("Coding", 2)]


def test_dashboard_period_toggle_refreshes(qtbot, tmp_config):
    _insert_on(date.today() - timedelta(days=40))

    window = MainWindow(
        timer=PomodoroTimer(),
        icon=QIcon(),
        cfg=tmp_config,
        notifier=MagicMock(spec=Notifier),
    )
    qtbot.addWidget(window)
    window.show()
    window.centralWidget().setCurrentIndex(2)

    page = window._dashboard_page
    assert page._val_sessions.text() == "0"
    page._set_period(None)
    assert page._val_sessions.text() == "1"
