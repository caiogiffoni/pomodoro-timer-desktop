import subprocess
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


class Notifier:
    def __init__(self, volume: int = 80):
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self.set_volume(volume)

    def set_volume(self, volume: int) -> None:
        """volume: 0–100"""
        self._audio.setVolume(max(0, min(100, volume)) / 100.0)

    def play_sound(self, path: str) -> None:
        p = Path(path).expanduser()
        if not p.exists():
            return
        self._player.setSource(QUrl.fromLocalFile(str(p)))
        self._player.play()

    def notify(self, title: str, body: str) -> None:
        try:
            subprocess.Popen(
                ["notify-send", "--app-name=Pomodoro", title, body],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # notify-send not installed — silent
