import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import config
from app.notifier import Notifier
from app.timer import PomodoroTimer
from app.window import MainWindow

_ASSETS = Path(__file__).parent / "assets"

_MESSAGES = {
    "work": ("Work session done!", "Time for a break."),
    "break": ("Break over!", "Back to work."),
}


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Pomodoro")

    config.seed(_ASSETS)
    cfg = config.load()

    icon = QIcon(str(_ASSETS / "icon.png"))
    timer = PomodoroTimer(
        work_minutes=cfg["work_duration"],
        break_minutes=cfg["break_duration"],
    )
    notifier = Notifier(volume=cfg["volume"])

    def on_phase_ended(phase: str) -> None:
        title, body = _MESSAGES.get(phase, ("Pomodoro", "Phase ended."))
        notifier.play_sound(cfg["selected_sound"])
        notifier.notify(title, body)

    timer.phase_ended.connect(on_phase_ended)

    window = MainWindow(timer=timer, icon=icon, cfg=cfg)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
