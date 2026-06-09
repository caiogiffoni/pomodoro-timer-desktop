from PyQt6.QtCore import Qt, QEvent, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.timer import Phase, PomodoroTimer

_COLOR_WORK = QColor("#D85A30")
_COLOR_BREAK = QColor("#1D9E75")
_COLOR_TRACK = QColor("#2E2E2E")
_COLOR_BG = QColor("#1A1A1A")
_COLOR_TEXT = QColor("#F0F0F0")

_ARC_MARGIN = 24
_ARC_WIDTH = 10


class _ArcWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fraction = 1.0
        self._phase = Phase.IDLE
        self._seconds_left = 0
        self.setMinimumSize(240, 240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_state(self, fraction: float, phase: Phase, seconds_left: int) -> None:
        self._fraction = fraction
        self._phase = phase
        self._seconds_left = seconds_left
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        rect = QRect(
            _ARC_MARGIN,
            _ARC_MARGIN,
            w - _ARC_MARGIN * 2,
            h - _ARC_MARGIN * 2,
        )

        # Background fill
        p.fillRect(0, 0, w, h, _COLOR_BG)

        # Track ring
        pen = QPen(_COLOR_TRACK, _ARC_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # Progress arc (depletes clockwise from top)
        if self._fraction > 0:
            color = _COLOR_WORK if self._phase == Phase.WORK else _COLOR_BREAK
            pen = QPen(color, _ARC_WIDTH)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            start_angle = 90 * 16
            span_angle = -int(self._fraction * 360 * 16)
            p.drawArc(rect, start_angle, span_angle)

        # Time label
        minutes, seconds = divmod(self._seconds_left, 60)
        label = f"{minutes:02d}:{seconds:02d}"
        p.setPen(QPen(_COLOR_TEXT))
        font = QFont("Monospace", 28, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

        p.end()


class MainWindow(QMainWindow):
    def __init__(self, timer: PomodoroTimer, icon: QIcon, cfg: dict, notifier=None, parent=None):
        super().__init__(parent)
        self._timer = timer
        self._cfg = cfg
        self._notifier = notifier
        self._total_seconds = timer.work_duration

        self.setWindowTitle("Pomodoro")
        self.setWindowIcon(icon)
        self.setFixedSize(300, 360)
        self.setStyleSheet(f"background-color: {_COLOR_BG.name()};")

        # Widgets
        self._arc = _ArcWidget()
        self._arc.set_state(1.0, Phase.IDLE, timer.work_duration)

        self._btn_start = QPushButton("Start")
        self._btn_start.setFixedSize(120, 40)
        self._btn_start.setStyleSheet(self._btn_style(_COLOR_WORK))
        self._btn_start.clicked.connect(self._on_start_stop)

        self._btn_gear = QPushButton("⚙")
        self._btn_gear.setFixedSize(36, 36)
        self._btn_gear.setStyleSheet(
            "color: #888; background: transparent; border: none; font-size: 18px;"
        )
        self._btn_gear.clicked.connect(self._on_settings)

        # Layout
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._btn_start)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_gear)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.addWidget(self._arc, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addLayout(btn_row)

        container = QWidget()
        container.setLayout(vbox)
        self.setCentralWidget(container)

        # Signals
        timer.tick.connect(self._on_tick)
        timer.phase_ended.connect(self._on_phase_ended)
        timer.stopped.connect(self._on_stopped)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_tick(self, seconds_left: int) -> None:
        fraction = seconds_left / self._total_seconds if self._total_seconds else 0
        self._arc.set_state(fraction, self._timer.phase, seconds_left)

    def _on_phase_ended(self, phase: str) -> None:
        if phase == "work":
            self._total_seconds = self._timer.break_duration
            self._btn_start.setStyleSheet(self._btn_style(_COLOR_BREAK))
            self._btn_start.setText("Stop")
        else:
            self._total_seconds = self._timer.work_duration
            self._btn_start.setStyleSheet(self._btn_style(_COLOR_WORK))
            self._btn_start.setText("Stop")

    def _on_stopped(self) -> None:
        self._total_seconds = self._timer.work_duration
        self._arc.set_state(1.0, Phase.IDLE, self._timer.work_duration)
        self._btn_start.setText("Start")
        self._btn_start.setStyleSheet(self._btn_style(_COLOR_WORK))

    def _on_start_stop(self) -> None:
        if self._timer.phase in (Phase.IDLE, Phase.STOPPED):
            self._total_seconds = self._timer.work_duration
            self._timer.start()
            self._btn_start.setText("Stop")
        else:
            self._timer.stop()

    def _on_settings(self) -> None:
        from app import config
        from app.settings import SettingsDialog
        dlg = SettingsDialog(cfg=self._cfg, notifier=self._notifier, parent=self)
        if dlg.exec():
            self._cfg = dlg.updated_cfg()
            config.save(self._cfg)
            self._timer.update_durations(
                self._cfg["work_duration"],
                self._cfg["break_duration"],
            )
            if self._notifier:
                self._notifier.set_volume(self._cfg["volume"])

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                self.hide()
                return
        super().changeEvent(event)

    # ------------------------------------------------------------------

    @staticmethod
    def _btn_style(color: QColor) -> str:
        return (
            f"QPushButton {{"
            f"  background-color: {color.name()};"
            f"  color: white;"
            f"  border-radius: 8px;"
            f"  font-size: 15px;"
            f"  font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{ background-color: {color.lighter(120).name()}; }}"
            f"QPushButton:pressed {{ background-color: {color.darker(120).name()}; }}"
        )
