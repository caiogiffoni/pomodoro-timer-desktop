import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import config
from app.timer import PomodoroTimer
from app.window import MainWindow

_ASSETS = Path(__file__).parent / "assets"


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
    window = MainWindow(timer=timer, icon=icon, cfg=cfg)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
