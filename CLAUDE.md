# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Pomodoro timer desktop app for Ubuntu (Linux). Python 3.14 + PyQt6, managed with `uv`.

## Stack

- **PyQt6** — main UI framework
- **QPainter** — circular arc countdown rendering
- **QSystemTrayIcon** — tray icon and context menu
- **QMediaPlayer** — alarm sound playback
- **notify-send** (subprocess) — desktop notifications

## Commands

```bash
# Activate venv
source .venv/bin/activate

# Install dependencies
uv pip install PyQt6

# Run app
uv run python main.py

# Run app (venv active)
python main.py
```

## Target structure

```
pomodoro/
├── main.py
├── app/
│   ├── __init__.py
│   ├── window.py     # main window + QPainter arc
│   ├── timer.py      # QTimer state machine, emits signals only
│   ├── settings.py   # QDialog: durations, volume, sound picker
│   ├── tray.py       # QSystemTrayIcon + context menu
│   └── notifier.py   # QMediaPlayer + notify-send subprocess
├── assets/
│   ├── alarm.wav
│   └── icon.png
└── requirements.txt
```

## Architecture

**Signal flow:** `timer.py` drives everything — it owns the `QTimer` tick and emits `tick(seconds_left)`, `phase_ended(phase)`, and `stopped()`. No widget imports allowed in `timer.py`.

**Config** persists to `~/.config/pomodoro/config.json`. On first launch, `main.py` seeds the config dir and copies `assets/alarm.wav` → `~/.config/pomodoro/sounds/default.wav`.

**State machine:** `IDLE → WORK (25min) → BREAK (5min) → WORK → …`. Any state can transition to `STOPPED → IDLE`.

**Colors:** work arc = `#D85A30` (red-orange), break arc = `#1D9E75` (teal).

## Config schema

```json
{
  "work_duration": 25,
  "break_duration": 5,
  "volume": 80,
  "selected_sound": "~/.config/pomodoro/sounds/default.wav"
}
```

---

## Build plan — incremental milestones

Trigger each milestone explicitly. Do not advance until the previous one is verified working.

### Milestone 1 — Scaffold + dependencies ✓
- [x] Add `PyQt6` to `pyproject.toml` dependencies
- [x] Create `app/__init__.py` (empty)
- [x] Create `assets/` placeholder (`icon.png`, `alarm.wav` stubs or real files)
- [x] Update `requirements.txt`
- [x] Verify: `uv run python main.py` prints something and exits cleanly

### Milestone 2 — Timer core (`timer.py`) ✓
- [x] Implement `PomodoroTimer(QObject)` with `QTimer`
- [x] State machine: `IDLE`, `WORK`, `BREAK`, `STOPPED`
- [x] Signals: `tick(int)`, `phase_ended(str)`, `stopped()`
- [x] Methods: `start()`, `stop()`, `skip()`
- [x] Zero UI or widget imports
- [x] Verify: instantiate and drive in a throwaway script, signals fire correctly

### Milestone 3 — Main window + arc (`window.py`) ✓
- [x] `MainWindow(QMainWindow)` with fixed size
- [x] `QPainter` arc that depletes clockwise; color switches by phase
- [x] Start/Stop button centered below arc
- [x] Gear icon button that opens (stubbed) settings dialog
- [x] Wire to `PomodoroTimer` signals — arc repaints on `tick`
- [x] Verify: window opens, arc animates, button starts/stops timer

### Milestone 4 — Config + first-launch seeding (`main.py`) ✓
- [x] `load_config()` / `save_config()` reading `~/.config/pomodoro/config.json`
- [x] First-launch: create sounds dir, copy `assets/alarm.wav` as `default.wav`
- [x] Pass config into window/timer on startup
- [x] Verify: config file created on first run, values survive restart

### Milestone 5 — Notifier (`notifier.py`)
- [ ] `Notifier` class: `play_sound(path, volume)` via `QMediaPlayer`
- [ ] `notify(title, body)` via `subprocess` + `notify-send`
- [ ] Called from `main.py` on `phase_ended` signal
- [ ] Verify: sound plays and desktop notification appears at phase end

### Milestone 6 — Tray icon (`tray.py`)
- [ ] `TrayIcon(QSystemTrayIcon)` with `icon.png`
- [ ] Tooltip updates on `tick` signal with remaining time
- [ ] Context menu: Show, Skip phase, Stop, Quit
- [ ] Verify: tray icon visible, tooltip updates, menu actions work

### Milestone 7 — Settings dialog (`settings.py`)
- [ ] `SettingsDialog(QDialog)` opened from gear icon
- [ ] Spinboxes: work duration, break duration
- [ ] Volume slider with live preview (plays sound at new volume)
- [ ] Sound file picker — opens `~/.config/pomodoro/sounds/`, copies selection there
- [ ] Saves to config on accept
- [ ] Verify: changes persist across restarts, live preview plays sound

### Milestone 8 — Polish + final QA
- [ ] Real `icon.png` (tray + window icon)
- [ ] Real `alarm.wav`
- [ ] Window title and taskbar name
- [ ] Handle missing `notify-send` gracefully (not installed = silent)
- [ ] Handle missing sound file gracefully
- [ ] Verify full loop: WORK → notification+sound → BREAK → notification+sound → WORK
