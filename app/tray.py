from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QRadialGradient, QBrush
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from app.timer import Phase, PomodoroTimer


def _make_dot_icon(color: QColor) -> QIcon:
    size = 64
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    grad = QRadialGradient(size * 0.38, size * 0.35, size * 0.5)
    grad.setColorAt(0.0, color.lighter(140))
    grad.setColorAt(0.6, color)
    grad.setColorAt(1.0, color.darker(140))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, size - 8, size - 8)

    p.end()
    return QIcon(pix)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, timer: PomodoroTimer, window, notifier=None, parent=None):
        super().__init__(icon, parent)
        self._timer = timer
        self._window = window
        self._notifier = notifier
        self._static_icon = icon
        self._icon_work = _make_dot_icon(QColor("#D85A30"))
        self._icon_break = _make_dot_icon(QColor("#1D9E75"))

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

        self._act_time = menu.addAction("⏱ Time remaining")
        self._act_time.triggered.connect(self._on_time_popup)
        self._act_time.setEnabled(False)

        menu.addSeparator()

        self._act_show = menu.addAction("Show")
        self._act_show.triggered.connect(self._on_show)

        self._act_pause = menu.addAction("Pause")
        self._act_pause.triggered.connect(self._on_pause_resume)
        self._act_pause.setEnabled(False)

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
        paused = self._timer.phase == Phase.PAUSED
        self._act_time.setEnabled(active or paused)
        self._act_pause.setEnabled(active or paused)
        self._act_pause.setText("Resume" if paused else "Pause")
        self._act_skip.setEnabled(active)
        self._act_stop.setEnabled(active or paused)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_tick(self, seconds_left: int) -> None:
        phase = self._timer.phase
        label = "Work" if phase == Phase.WORK else "Break"
        minutes, seconds = divmod(seconds_left, 60)
        self.setToolTip(f"Pomodoro — {label} {minutes:02d}:{seconds:02d}")
        self.setIcon(self._icon_work if phase == Phase.WORK else self._icon_break)
        self._update_actions()

    def _on_stopped(self) -> None:
        self.setToolTip("Pomodoro")
        self.setIcon(self._static_icon)
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
        if self._notifier is None:
            return
        phase = self._timer.phase
        if phase == Phase.WORK:
            minutes, seconds = divmod(self._timer.seconds_left, 60)
            self._notifier.notify("Work session", f"{minutes:02d}:{seconds:02d} remaining")
        elif phase == Phase.BREAK:
            minutes, seconds = divmod(self._timer.seconds_left, 60)
            self._notifier.notify("Break", f"{minutes:02d}:{seconds:02d} remaining")
        else:
            self._notifier.notify("Pomodoro", "No session running")

    def _on_pause_resume(self) -> None:
        if self._timer.phase == Phase.PAUSED:
            self._timer.resume()
        else:
            self._timer.pause()
        self._update_actions()

    def _on_quit(self) -> None:
        self._timer.stop()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
