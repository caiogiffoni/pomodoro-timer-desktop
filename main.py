import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import config, stats
from app.notifier import Notifier
from app.timer import PomodoroTimer
from app.tray import TrayIcon
from app.window import MainWindow

_ASSETS = Path(__file__).parent / "assets"

_MESSAGES = {
    "work": ("Work session done!", "Time for a break."),
    "break": ("Break over!", "Back to work."),
    "long_break": ("Long break over!", "Back to work."),
}


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Pomodoro")
    app.setQuitOnLastWindowClosed(False)

    config.seed(_ASSETS)
    config.install_desktop_file(Path(__file__), _ASSETS / "icon.png")
    app.setDesktopFileName("pomodoro")
    cfg = config.load()

    icon = QIcon(str(_ASSETS / "icon.png"))
    app.setWindowIcon(icon)
    timer = PomodoroTimer(
        work_minutes=cfg["work_duration"],
        break_minutes=cfg["break_duration"],
        long_break_minutes=cfg["long_break_duration"],
        pomodoros_until_long_break=cfg["pomodoros_until_long_break"],
        auto_start_break=cfg.get("auto_start_break", False),
    )
    notifier = Notifier(volume=cfg["volume"])

    window = MainWindow(timer=timer, icon=icon, cfg=cfg, notifier=notifier)
    window.show()

    tray = TrayIcon(icon=icon, timer=timer, window=window, notifier=notifier)
    tray.show()

    def stop_alarm(_=None) -> None:
        notifier.stop_repeating()
        tray.set_alarm_active(False)

    def on_phase_ended(phase: str) -> None:
        title, body = _MESSAGES.get(phase, ("Pomodoro", "Phase ended."))
        notifier.play_sound(cfg["selected_sound"])
        notifier.notify(title, body)
        if phase == "work":
            stats.record_session()
            tray._update_stats_label()
        elif phase in ("break", "long_break"):
            notifier.start_repeating(cfg["selected_sound"], cfg["repeat_interval"])
            tray.set_alarm_active(True)

    timer.phase_ended.connect(on_phase_ended)
    timer.tick.connect(stop_alarm)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
