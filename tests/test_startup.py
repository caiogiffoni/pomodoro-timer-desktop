"""
Tests for TESTING.md sections 1 and 2:
  1 — App startup
  2 — Timer basic work session
"""

from PyQt6.QtCore import Qt

from app.timer import Phase


# ── Section 1: App startup ─────────────────────────────────────────────────────


def test_window_is_visible(app_window):
    window, _ = app_window
    assert window.isVisible()


def test_window_title(app_window):
    window, _ = app_window
    assert window.windowTitle() == "Pomodoro"


def test_window_shows_full_arc_at_25_00(app_window):
    window, timer = app_window
    assert window._arc._seconds_left == timer.work_duration  # 1500 s
    assert window._arc._fraction == 1.0
    assert window._arc._phase == Phase.IDLE


def test_timer_tab_is_default(app_window):
    window, _ = app_window
    assert window.centralWidget().currentIndex() == 0


def test_stats_tab_shows_today_count(app_window, qtbot):
    window, _ = app_window
    window.centralWidget().setCurrentIndex(1)
    qtbot.waitUntil(
        lambda: "today" in window._stats_page._lbl_goal.text(), timeout=1000
    )
    assert "0 today" in window._stats_page._lbl_goal.text()


# ── Section 2: Timer — basic work session ─────────────────────────────────────


def test_start_button_label_and_pause_appear(app_window, qtbot):
    window, _ = app_window
    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)
    assert window._btn_start.text() == "Stop"
    assert window._btn_pause.isVisible()
    assert window._btn_pause.text() == "Pause"


def test_start_begins_countdown(app_window, qtbot):
    window, timer = app_window
    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)
    with qtbot.waitSignal(timer.tick, timeout=2000):
        pass
    assert timer.seconds_left < timer.work_duration
    assert timer.phase == Phase.WORK


def test_arc_depletes_after_start(app_window, qtbot):
    window, timer = app_window
    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)
    with qtbot.waitSignal(timer.tick, timeout=2000):
        pass
    assert window._arc._fraction < 1.0


def test_pause_freezes_timer(app_window, qtbot):
    window, timer = app_window
    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)
    qtbot.waitSignal(timer.tick, timeout=2000)

    qtbot.mouseClick(window._btn_pause, Qt.MouseButton.LeftButton)

    assert timer.phase == Phase.PAUSED
    assert window._btn_pause.text() == "Resume"

    frozen = timer.seconds_left
    qtbot.wait(1500)
    assert timer.seconds_left == frozen


def test_resume_continues_from_paused_time(app_window, qtbot):
    window, timer = app_window
    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)
    qtbot.waitSignal(timer.tick, timeout=2000)

    qtbot.mouseClick(window._btn_pause, Qt.MouseButton.LeftButton)
    paused_at = timer.seconds_left

    qtbot.mouseClick(window._btn_pause, Qt.MouseButton.LeftButton)  # Resume

    assert timer.phase == Phase.WORK
    assert window._btn_pause.text() == "Pause"
    with qtbot.waitSignal(timer.tick, timeout=2000):
        pass
    assert timer.seconds_left < paused_at


def test_stop_resets_window_to_idle(app_window, qtbot):
    window, timer = app_window
    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)
    qtbot.waitSignal(timer.tick, timeout=2000)

    qtbot.mouseClick(window._btn_start, Qt.MouseButton.LeftButton)  # Stop

    assert window._btn_start.text() == "Start"
    assert not window._btn_pause.isVisible()
    assert window._arc._seconds_left == timer.work_duration
    assert window._arc._fraction == 1.0
