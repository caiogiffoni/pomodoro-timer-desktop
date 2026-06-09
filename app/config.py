import json
import shutil
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "pomodoro"
_CONFIG_FILE = _CONFIG_DIR / "config.json"
_SOUNDS_DIR = _CONFIG_DIR / "sounds"

_DEFAULTS = {
    "work_duration": 25,
    "break_duration": 5,
    "volume": 80,
    "selected_sound": str(_SOUNDS_DIR / "default.wav"),
}


def seed(assets_dir: Path) -> None:
    """Create config dir and copy default alarm on first launch."""
    _SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    default_wav = _SOUNDS_DIR / "default.wav"
    if not default_wav.exists():
        src = assets_dir / "alarm.wav"
        if src.exists():
            shutil.copy2(src, default_wav)
    if not _CONFIG_FILE.exists():
        _CONFIG_FILE.write_text(json.dumps(_DEFAULTS, indent=2))


def load() -> dict:
    seed_needed = not _CONFIG_FILE.exists()
    if seed_needed:
        return dict(_DEFAULTS)
    try:
        data = json.loads(_CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)
    return {**_DEFAULTS, **data}


def save(cfg: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
