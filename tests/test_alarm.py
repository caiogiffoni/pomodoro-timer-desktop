"""Section 6: break alarm auto-stops after configurable timeout."""

import pytest
from unittest.mock import MagicMock
from app.notifier import Notifier


@pytest.fixture
def notifier(qtbot):
    n = Notifier(volume=0)
    n.play_sound = MagicMock()
    yield n
    n.stop_repeating()


def test_timeout_zero_never_auto_stops(notifier):
    notifier.start_repeating("/fake/alarm.wav", interval_seconds=30, timeout_seconds=0)
    assert notifier.is_repeating
    assert not notifier._stop_timer.isActive()


def test_timeout_nonzero_activates_stop_timer(notifier):
    notifier.start_repeating("/fake/alarm.wav", interval_seconds=30, timeout_seconds=180)
    assert notifier._stop_timer.isActive()
    assert notifier._stop_timer.interval() == 180 * 1000


def test_alarm_stops_when_timeout_fires(notifier):
    notifier.start_repeating("/fake/alarm.wav", interval_seconds=30, timeout_seconds=180)
    notifier._stop_timer.timeout.emit()
    assert not notifier.is_repeating


def test_manual_stop_also_cancels_timeout(notifier):
    notifier.start_repeating("/fake/alarm.wav", interval_seconds=30, timeout_seconds=180)
    notifier.stop_repeating()
    assert not notifier._stop_timer.isActive()
