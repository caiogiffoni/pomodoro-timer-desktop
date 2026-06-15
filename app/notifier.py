import subprocess
from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


class Notifier:
    def __init__(self, volume: int = 80):
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self.set_volume(volume)

        self._repeat_timer = QTimer()
        self._repeat_path = ""
        self._repeat_timer.timeout.connect(lambda: self.play_sound(self._repeat_path))

    def set_volume(self, volume: int) -> None:
        """volume: 0–100"""
        self._audio.setVolume(max(0, min(100, volume)) / 100.0)

    def play_sound(self, path: str) -> None:
        p = Path(path).expanduser()
        if not p.exists():
            return
        self._player.setSource(QUrl.fromLocalFile(str(p)))
        self._player.play()

    def start_repeating(self, path: str, interval_seconds: int) -> None:
        self._repeat_path = path
        self._repeat_timer.setInterval(max(1, interval_seconds) * 1000)
        self._repeat_timer.start()

    def stop_repeating(self) -> None:
        self._repeat_timer.stop()

    @property
    def is_repeating(self) -> bool:
        return self._repeat_timer.isActive()

    def notify(self, title: str, body: str) -> None:
        try:
            subprocess.Popen(
                ["notify-send", "--app-name=Pomodoro", title, body],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # notify-send not installed — silent
