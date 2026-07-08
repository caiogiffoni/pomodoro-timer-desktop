"""Section 9: long break cycle — every N pomodoros triggers a long break, then resets."""

import pytest
from app.timer import Phase, PomodoroTimer


@pytest.fixture
def cycle_timer():
    return PomodoroTimer(
        work_minutes=1,
        break_minutes=1,
        long_break_minutes=2,
        pomodoros_until_long_break=2,
        auto_start_break=True,
    )


def test_second_work_triggers_long_break(cycle_timer):
    cycle_timer.start()
    cycle_timer.skip()  # work 1 → break
    cycle_timer.skip()  # break → work 2
    cycle_timer.skip()  # work 2 → long break
    assert cycle_timer.phase == Phase.LONG_BREAK


def test_long_break_resets_session_counter(cycle_timer):
    cycle_timer.start()
    cycle_timer.skip()  # work 1 → break
    cycle_timer.skip()  # break → work 2
    cycle_timer.skip()  # work 2 → long break
    cycle_timer._seconds_left = 1
    cycle_timer._on_tick()  # natural expiry resets sessions_completed
    assert cycle_timer.sessions_completed == 0


def test_cycle_repeats_after_long_break(cycle_timer):
    cycle_timer.start()
    cycle_timer.skip()  # work 1 → break
    cycle_timer.skip()  # break → work 2
    cycle_timer.skip()  # work 2 → long break
    cycle_timer._seconds_left = 1
    cycle_timer._on_tick()  # long break expires → IDLE
    cycle_timer.start()    # new cycle, work 1
    cycle_timer.skip()     # → regular break (not long break)
    assert cycle_timer.phase == Phase.BREAK
