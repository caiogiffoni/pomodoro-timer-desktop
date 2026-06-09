from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from app.timer import Phase, PomodoroTimer


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, timer: PomodoroTimer, window, parent=None):
        super().__init__(icon, parent)
        self._timer = timer
        self._window = window

        self.setToolTip("Pomodoro")
        self._build_menu()

        self.activated.connect(self._on_activated)
        timer.tick.connect(self._on_tick)
        timer.stopped.connect(self._on_stopped)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menu = QMenu()

        self._act_show = menu.addAction("Show")
        self._act_show.triggered.connect(self._on_show)

        self._act_skip = menu.addAction("Skip phase")
        self._act_skip.triggered.connect(self._timer.skip)
        self._act_skip.setEnabled(False)

        self._act_stop = menu.addAction("Stop")
        self._act_stop.triggered.connect(self._timer.stop)
        self._act_stop.setEnabled(False)

        menu.addSeparator()

        act_quit = menu.addAction("Quit")
        act_quit.triggered.connect(self._on_quit)

        self.setContextMenu(menu)

    def _update_actions(self) -> None:
        active = self._timer.phase in (Phase.WORK, Phase.BREAK)
        self._act_skip.setEnabled(active)
        self._act_stop.setEnabled(active)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_tick(self, seconds_left: int) -> None:
        phase = self._timer.phase
        label = "Work" if phase == Phase.WORK else "Break"
        minutes, seconds = divmod(seconds_left, 60)
        self.setToolTip(f"Pomodoro — {label} {minutes:02d}:{seconds:02d}")
        self._update_actions()

    def _on_stopped(self) -> None:
        self.setToolTip("Pomodoro")
        self._update_actions()

    def _on_show(self) -> None:
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._on_time_popup()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show()

    def _on_time_popup(self) -> None:
        phase = self._timer.phase
        if phase == Phase.WORK:
            minutes, seconds = divmod(self._timer.seconds_left, 60)
            self.showMessage(
                "Work session",
                f"{minutes:02d}:{seconds:02d} remaining",
                QSystemTrayIcon.MessageIcon.NoIcon,
                3000,
            )
        elif phase == Phase.BREAK:
            minutes, seconds = divmod(self._timer.seconds_left, 60)
            self.showMessage(
                "Break",
                f"{minutes:02d}:{seconds:02d} remaining",
                QSystemTrayIcon.MessageIcon.NoIcon,
                3000,
            )
        else:
            self.showMessage(
                "Pomodoro",
                "No session running",
                QSystemTrayIcon.MessageIcon.NoIcon,
                2000,
            )

    def _on_quit(self) -> None:
        self._timer.stop()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
