import json
import shutil
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "pomodoro"
_CONFIG_FILE = _CONFIG_DIR / "config.json"
_SOUNDS_DIR = _CONFIG_DIR / "sounds"
_DESKTOP_FILE = Path.home() / ".local" / "share" / "applications" / "pomodoro.desktop"

_DEFAULTS = {
    "work_duration": 25,
    "break_duration": 5,
    "long_break_duration": 15,
    "pomodoros_until_long_break": 4,
    "volume": 80,
    "selected_sound": str(_SOUNDS_DIR / "default.wav"),
    "repeat_interval": 30,
    "auto_start_break": False,
}


_BUNDLED_SOUNDS = {
    "default.wav": "alarm.wav",
    "bell.wav": "bell.wav",
    "digital.wav": "digital.wav",
    "soft.wav": "soft.wav",
}


def seed(assets_dir: Path) -> None:
    """Create config dir and copy bundled sounds on first launch."""
    _SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for dest_name, src_name in _BUNDLED_SOUNDS.items():
        dest = _SOUNDS_DIR / dest_name
        if not dest.exists():
            src = assets_dir / src_name
            if src.exists():
                shutil.copy2(src, dest)
    if not _CONFIG_FILE.exists():
        _CONFIG_FILE.write_text(json.dumps(_DEFAULTS, indent=2))


def install_desktop_file(main_py: Path, icon_path: Path) -> None:
    """Write ~/.local/share/applications/pomodoro.desktop so GNOME dock shows the correct icon."""
    _DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Name=Pomodoro Timer\n"
        "Type=Application\n"
        f"Exec=uv run python {main_py.resolve()}\n"
        f"Icon={icon_path.resolve()}\n"
        "Terminal=false\n"
        "StartupWMClass=Pomodoro\n"
        "Categories=Utility;\n"
    )
    _DESKTOP_FILE.write_text(content)


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
