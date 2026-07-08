"""Section 13: session stats written to DB and shown correctly in the Stats tab."""

from unittest.mock import MagicMock
from PyQt6.QtGui import QIcon

from app import stats
from app.notifier import Notifier
from app.timer import PomodoroTimer
from app.window import MainWindow


def _record():
    stats.begin_session(planned_duration_seconds=1500, pomodoro_number=1)
    return stats.record_session()


def test_completed_sessions_counted(tmp_config):
    assert stats.today_count() == 0
    _record()
    _record()
    assert stats.today_count() == 2


def test_early_stop_not_counted(tmp_config):
    stats.begin_session(planned_duration_seconds=1500, pomodoro_number=1)
    # record_session never called — completed_at stays NULL
    assert stats.today_count() == 0


def test_stats_tab_reflects_db_on_fresh_window(qtbot, tmp_config):
    _record()
    _record()
    _record()

    window = MainWindow(
        timer=PomodoroTimer(),
        icon=QIcon(),
        cfg=tmp_config,
        notifier=MagicMock(spec=Notifier),
    )
    qtbot.addWidget(window)
    window.show()
    window.centralWidget().setCurrentIndex(1)
    qtbot.waitUntil(lambda: "3 today" in window._stats_page._lbl_goal.text(), timeout=1000)
