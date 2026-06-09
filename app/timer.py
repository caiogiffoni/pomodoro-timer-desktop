from enum import Enum, auto

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class Phase(Enum):
    IDLE = auto()
    WORK = auto()
    BREAK = auto()
    PAUSED = auto()
    STOPPED = auto()


class PomodoroTimer(QObject):
    tick = pyqtSignal(int)         # seconds remaining
    phase_ended = pyqtSignal(str)  # "work" or "break"
    paused = pyqtSignal()
    resumed = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, work_minutes: int = 25, break_minutes: int = 5, parent=None):
        super().__init__(parent)
        self.work_duration = work_minutes * 60
        self.break_duration = break_minutes * 60

        self._phase = Phase.IDLE
        self._seconds_left = 0
        self._phase_before_pause: Phase = Phase.IDLE

        self._qtimer = QTimer(self)
        self._qtimer.setInterval(1000)
        self._qtimer.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def seconds_left(self) -> int:
        return self._seconds_left

    def start(self) -> None:
        if self._phase in (Phase.IDLE, Phase.STOPPED):
            self._enter_work()

    def pause(self) -> None:
        if self._phase in (Phase.WORK, Phase.BREAK):
            self._qtimer.stop()
            self._phase_before_pause = self._phase
            self._phase = Phase.PAUSED
            self.paused.emit()

    def resume(self) -> None:
        if self._phase == Phase.PAUSED:
            self._phase = self._phase_before_pause
            self._qtimer.start()
            self.resumed.emit()

    def stop(self) -> None:
        if self._phase in (Phase.WORK, Phase.BREAK, Phase.PAUSED):
            self._qtimer.stop()
            self._phase = Phase.STOPPED
            self._seconds_left = 0
            self.stopped.emit()

    def skip(self) -> None:
        if self._phase == Phase.WORK:
            self._qtimer.stop()
            self.phase_ended.emit("work")
            self._enter_break()
        elif self._phase == Phase.BREAK:
            self._qtimer.stop()
            self.phase_ended.emit("break")
            self._enter_work()

    def update_durations(self, work_minutes: int, break_minutes: int) -> None:
        self.work_duration = work_minutes * 60
        self.break_duration = break_minutes * 60

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _enter_work(self) -> None:
        self._phase = Phase.WORK
        self._seconds_left = self.work_duration
        self.tick.emit(self._seconds_left)
        self._qtimer.start()

    def _enter_break(self) -> None:
        self._phase = Phase.BREAK
        self._seconds_left = self.break_duration
        self.tick.emit(self._seconds_left)
        self._qtimer.start()

    def _on_tick(self) -> None:
        self._seconds_left -= 1
        self.tick.emit(self._seconds_left)
        if self._seconds_left <= 0:
            self._qtimer.stop()
            ended_phase = "work" if self._phase == Phase.WORK else "break"
            self.phase_ended.emit(ended_phase)
            if ended_phase == "work":
                self._enter_break()
            else:
                self._phase = Phase.IDLE
                self._seconds_left = 0
                self.stopped.emit()
