from enum import Enum, auto

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class Phase(Enum):
    IDLE = auto()
    WORK = auto()
    BREAK = auto()
    LONG_BREAK = auto()
    PAUSED = auto()
    STOPPED = auto()


class PomodoroTimer(QObject):
    tick = pyqtSignal(int)           # seconds remaining
    phase_started = pyqtSignal(str)  # "work", "break", or "long_break"
    phase_ended = pyqtSignal(str)    # "work", "break", or "long_break"
    paused = pyqtSignal()
    resumed = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(
        self,
        work_minutes: int = 25,
        break_minutes: int = 5,
        long_break_minutes: int = 15,
        pomodoros_until_long_break: int = 4,
        auto_start_break: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.work_duration = work_minutes * 60
        self.break_duration = break_minutes * 60
        self.long_break_duration = long_break_minutes * 60
        self.pomodoros_until_long_break = pomodoros_until_long_break
        self.auto_start_break = auto_start_break

        self._phase = Phase.IDLE
        self._seconds_left = 0
        self._phase_before_pause: Phase = Phase.IDLE
        self._sessions_completed = 0
        self._pending_break: Phase | None = None

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

    @property
    def sessions_completed(self) -> int:
        return self._sessions_completed

    @property
    def next_is_long_break(self) -> bool:
        return self._sessions_completed % self.pomodoros_until_long_break == 0

    @property
    def pending_break(self) -> "Phase | None":
        return self._pending_break

    def start(self) -> None:
        if self._phase in (Phase.IDLE, Phase.STOPPED):
            if self._pending_break is not None:
                pending = self._pending_break
                self._pending_break = None
                if pending == Phase.LONG_BREAK:
                    self._enter_long_break()
                else:
                    self._enter_break()
            else:
                self._enter_work()

    def pause(self) -> None:
        if self._phase in (Phase.WORK, Phase.BREAK, Phase.LONG_BREAK):
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
        if self._phase in (Phase.WORK, Phase.BREAK, Phase.LONG_BREAK, Phase.PAUSED):
            self._qtimer.stop()
            self._pending_break = None
            self._phase = Phase.STOPPED
            self._seconds_left = 0
            self.stopped.emit()

    def skip(self) -> None:
        if self._phase == Phase.WORK:
            self._qtimer.stop()
            self._sessions_completed += 1
            self.phase_ended.emit("work")
            if self.auto_start_break:
                if self.next_is_long_break:
                    self._enter_long_break()
                else:
                    self._enter_break()
            else:
                self._pending_break = Phase.LONG_BREAK if self.next_is_long_break else Phase.BREAK
                self._seconds_left = self.long_break_duration if self._pending_break == Phase.LONG_BREAK else self.break_duration
                self._phase = Phase.IDLE
                self.stopped.emit()
        elif self._phase in (Phase.BREAK, Phase.LONG_BREAK):
            label = "break" if self._phase == Phase.BREAK else "long_break"
            self._qtimer.stop()
            self.phase_ended.emit(label)
            self._enter_work()

    def reset_sessions(self) -> None:
        self._sessions_completed = 0

    def update_durations(
        self,
        work_minutes: int,
        break_minutes: int,
        long_break_minutes: int,
        pomodoros_until_long_break: int,
    ) -> None:
        self.work_duration = work_minutes * 60
        self.break_duration = break_minutes * 60
        self.long_break_duration = long_break_minutes * 60
        self.pomodoros_until_long_break = pomodoros_until_long_break

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _enter_work(self) -> None:
        self._phase = Phase.WORK
        self._seconds_left = self.work_duration
        self.phase_started.emit("work")
        self.tick.emit(self._seconds_left)
        self._qtimer.start()

    def _enter_break(self) -> None:
        self._phase = Phase.BREAK
        self._seconds_left = self.break_duration
        self.phase_started.emit("break")
        self.tick.emit(self._seconds_left)
        self._qtimer.start()

    def _enter_long_break(self) -> None:
        self._phase = Phase.LONG_BREAK
        self._seconds_left = self.long_break_duration
        self.phase_started.emit("long_break")
        self.tick.emit(self._seconds_left)
        self._qtimer.start()

    def _on_tick(self) -> None:
        self._seconds_left -= 1
        self.tick.emit(self._seconds_left)
        if self._seconds_left <= 0:
            self._qtimer.stop()
            if self._phase == Phase.WORK:
                self._sessions_completed += 1
                self.phase_ended.emit("work")
                if self.auto_start_break:
                    if self.next_is_long_break:
                        self._enter_long_break()
                    else:
                        self._enter_break()
                else:
                    self._pending_break = Phase.LONG_BREAK if self.next_is_long_break else Phase.BREAK
                    self._seconds_left = self.long_break_duration if self._pending_break == Phase.LONG_BREAK else self.break_duration
                    self._phase = Phase.IDLE
                    self.stopped.emit()
            elif self._phase == Phase.BREAK:
                self.phase_ended.emit("break")
                self._phase = Phase.IDLE
                self._seconds_left = 0
                self.stopped.emit()
            elif self._phase == Phase.LONG_BREAK:
                self._sessions_completed = 0
                self.phase_ended.emit("long_break")
                self._phase = Phase.IDLE
                self._seconds_left = 0
                self.stopped.emit()
