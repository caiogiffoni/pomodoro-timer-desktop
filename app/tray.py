from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from app.timer import Phase, PomodoroTimer


def _make_phase_icon(base_icon: QIcon, color: QColor) -> QIcon:
    size = 64
    ring = 6  # ring thickness

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Tomato scaled to leave room for the ring
    inner = size - ring * 2
    tomato = base_icon.pixmap(inner, inner)
    p.drawPixmap(ring, ring, tomato)

    # Colored ring around it
    pen = QPen(color, ring)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    offset = ring // 2
    p.drawEllipse(QRect(offset, offset, size - ring, size - ring))

    p.end()
    return QIcon(pix)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, timer: PomodoroTimer, window, notifier=None, parent=None):
        super().__init__(icon, parent)
        self._timer = timer
        self._window = window
        self._notifier = notifier
        self._static_icon = icon
        self._icon_work = _make_phase_icon(icon, QColor("#D85A30"))
        self._icon_break = _make_phase_icon(icon, QColor("#1D9E75"))
        self._icon_long_break = _make_phase_icon(icon, QColor("#5B6AE8"))

        self.setToolTip("Pomodoro")
        self._build_menu()

        self.activated.connect(self._on_activated)
        timer.tick.connect(self._on_tick)
        timer.tick.connect(lambda _: self._update_time_label())
        timer.paused.connect(self._update_time_label)
        timer.resumed.connect(self._update_time_label)
        timer.stopped.connect(self._on_stopped)
        self._update_actions()

    def set_alarm_active(self, active: bool) -> None:
        self._act_dismiss.setVisible(active)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menu = QMenu()

        self._act_time_label = menu.addAction("Not running")
        self._act_time_label.setEnabled(False)

        self._act_stats_label = menu.addAction("")
        self._act_stats_label.setEnabled(False)
        self._update_stats_label()

        menu.addSeparator()

        self._act_dismiss = menu.addAction("Dismiss alarm")
        self._act_dismiss.triggered.connect(self._on_dismiss)
        self._act_dismiss.setVisible(False)

        self._act_show = menu.addAction("Show")
        self._act_show.triggered.connect(self._on_show)

        self._act_start = menu.addAction("Start")
        self._act_start.triggered.connect(self._timer.start)

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

        menu.aboutToShow.connect(self._update_time_label)
        menu.aboutToShow.connect(self._update_stats_label)
        self.setContextMenu(menu)

    def _update_actions(self) -> None:
        active = self._timer.phase in (Phase.WORK, Phase.BREAK, Phase.LONG_BREAK)
        paused = self._timer.phase == Phase.PAUSED
        idle = self._timer.phase in (Phase.IDLE, Phase.STOPPED)
        self._act_start.setEnabled(idle)
        self._act_pause.setEnabled(active or paused)
        self._act_pause.setText("Resume" if paused else "Pause")
        self._act_skip.setEnabled(active)
        self._act_stop.setEnabled(active or paused)

    def _update_time_label(self) -> None:
        phase = self._timer.phase
        minutes, seconds = divmod(self._timer.seconds_left, 60)
        if phase == Phase.WORK:
            self._act_time_label.setText(f"Work  {minutes:02d}:{seconds:02d}")
        elif phase == Phase.BREAK:
            self._act_time_label.setText(f"Break  {minutes:02d}:{seconds:02d}")
        elif phase == Phase.LONG_BREAK:
            self._act_time_label.setText(f"Long break  {minutes:02d}:{seconds:02d}")
        elif phase == Phase.PAUSED:
            self._act_time_label.setText(f"Paused  {minutes:02d}:{seconds:02d}")
        else:
            self._act_time_label.setText("Not running")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_tick(self, seconds_left: int) -> None:
        phase = self._timer.phase
        minutes, seconds = divmod(seconds_left, 60)
        if phase == Phase.WORK:
            label, icon = "Work", self._icon_work
        elif phase == Phase.LONG_BREAK:
            label, icon = "Long break", self._icon_long_break
        else:
            label, icon = "Break", self._icon_break
        self.setToolTip(f"Pomodoro — {label} {minutes:02d}:{seconds:02d}")
        self.setIcon(icon)
        self._update_actions()

    def _on_stopped(self) -> None:
        self.setToolTip("Pomodoro")
        self.setIcon(self._static_icon)
        self._update_actions()
        self._update_stats_label()

    def _update_stats_label(self) -> None:
        from app import stats
        n = stats.today_count()
        self._act_stats_label.setText(f"Today: {n} pomodoro{'s' if n != 1 else ''}")

    def _on_show(self) -> None:
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show()

    def _on_pause_resume(self) -> None:
        if self._timer.phase == Phase.PAUSED:
            self._timer.resume()
        else:
            self._timer.pause()
        self._update_actions()

    def _on_dismiss(self) -> None:
        if self._notifier:
            self._notifier.stop_repeating()
        self.set_alarm_active(False)

    def _on_quit(self) -> None:
        self._timer.stop()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
