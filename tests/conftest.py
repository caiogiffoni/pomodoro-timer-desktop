import json
from unittest.mock import MagicMock

import pytest
from PyQt6.QtGui import QIcon

from app.notifier import Notifier
from app.timer import PomodoroTimer
from app.window import MainWindow


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Redirect config and DB away from ~/.config/pomodoro so tests are isolated."""
    import app.config as cfg_mod
    import app.stats as stats_mod

    config_dir = tmp_path / "pomodoro"
    config_dir.mkdir()
    sounds_dir = config_dir / "sounds"
    sounds_dir.mkdir()

    monkeypatch.setattr(cfg_mod, "_CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg_mod, "_CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(cfg_mod, "_SOUNDS_DIR", sounds_dir)
    monkeypatch.setattr(stats_mod, "_DB_PATH", config_dir / "pomodoro.db")

    cfg = {
        "work_duration": 25,
        "break_duration": 5,
        "long_break_duration": 15,
        "pomodoros_until_long_break": 4,
        "volume": 80,
        "selected_sound": str(sounds_dir / "default.wav"),
        "repeat_interval": 30,
        "alarm_timeout": 3,
        "auto_start_break": False,
        "daily_goal": 0,
    }
    (config_dir / "config.json").write_text(json.dumps(cfg))
    stats_mod.init_db()
    return cfg


@pytest.fixture
def timer():
    return PomodoroTimer(work_minutes=25, break_minutes=5, auto_start_break=False)


@pytest.fixture
def app_window(qtbot, tmp_config, timer):
    """MainWindow wired to a real timer and a mock Notifier (no sound/files needed)."""
    notifier = MagicMock(spec=Notifier)
    window = MainWindow(timer=timer, icon=QIcon(), cfg=tmp_config, notifier=notifier)
    qtbot.addWidget(window)
    window.show()
    return window, timer
