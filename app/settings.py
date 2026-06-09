import shutil
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

_SOUNDS_DIR = Path.home() / ".config" / "pomodoro" / "sounds"


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, notifier, parent=None):
        super().__init__(parent)
        self._cfg = dict(cfg)
        self._notifier = notifier

        self.setWindowTitle("Settings")
        self.setFixedWidth(340)
        self.setModal(True)

        # --- Work duration ---
        self._spin_work = QSpinBox()
        self._spin_work.setRange(1, 120)
        self._spin_work.setSuffix(" min")
        self._spin_work.setValue(cfg["work_duration"])

        # --- Break duration ---
        self._spin_break = QSpinBox()
        self._spin_break.setRange(1, 60)
        self._spin_break.setSuffix(" min")
        self._spin_break.setValue(cfg["break_duration"])

        # --- Volume ---
        self._slider_vol = QSlider(Qt.Orientation.Horizontal)
        self._slider_vol.setRange(0, 100)
        self._slider_vol.setValue(cfg["volume"])
        self._lbl_vol = QLabel(str(cfg["volume"]))
        self._lbl_vol.setFixedWidth(28)
        self._slider_vol.valueChanged.connect(self._on_volume_changed)

        vol_row = QHBoxLayout()
        vol_row.addWidget(self._slider_vol)
        vol_row.addWidget(self._lbl_vol)

        # --- Sound picker ---
        self._lbl_sound = QLabel(self._short_name(cfg["selected_sound"]))
        self._lbl_sound.setWordWrap(True)
        self._btn_pick = QPushButton("Browse…")
        self._btn_pick.clicked.connect(self._on_pick_sound)

        sound_row = QHBoxLayout()
        sound_row.addWidget(self._lbl_sound, stretch=1)
        sound_row.addWidget(self._btn_pick)

        # --- Form ---
        form = QFormLayout()
        form.addRow("Work duration:", self._spin_work)
        form.addRow("Break duration:", self._spin_break)
        form.addRow("Volume:", vol_row)
        form.addRow("Alarm sound:", sound_row)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    def updated_cfg(self) -> dict:
        return {
            **self._cfg,
            "work_duration": self._spin_work.value(),
            "break_duration": self._spin_break.value(),
            "volume": self._slider_vol.value(),
            "selected_sound": self._cfg["selected_sound"],
        }

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_volume_changed(self, value: int) -> None:
        self._lbl_vol.setText(str(value))
        self._notifier.set_volume(value)
        self._notifier.play_sound(self._cfg["selected_sound"])

    def _on_pick_sound(self) -> None:
        _SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select alarm sound",
            str(_SOUNDS_DIR),
            "Audio files (*.wav *.mp3 *.ogg *.flac);;All files (*)",
        )
        if not path:
            return
        src = Path(path)
        dest = _SOUNDS_DIR / src.name
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        self._cfg["selected_sound"] = str(dest)
        self._lbl_sound.setText(self._short_name(str(dest)))

    # ------------------------------------------------------------------

    @staticmethod
    def _short_name(path: str) -> str:
        return Path(path).name
