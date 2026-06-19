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
# First-time setup (installs system deps, uv, Python 3.14, PyQt6, creates launcher)
./setup.sh

# Run
uv run python main.py
# or, after setup.sh:
pomodoro
```

## Structure

```
├── main.py              # boot: seeds config+db, wires all modules
├── setup.sh             # one-command install: apt deps + uv + PyQt6 + launcher
├── app/
│   ├── timer.py         # QTimer state machine — no UI imports
│   ├── window.py        # MainWindow + QPainter arc + Stats tab
│   ├── tray.py          # QSystemTrayIcon + context menu
│   ├── notifier.py      # QMediaPlayer + notify-send
│   ├── settings.py      # QDialog: durations, volume, sound picker, goal
│   ├── config.py        # load/save ~/.config/pomodoro/config.json
│   └── stats.py         # record/query ~/.config/pomodoro/stats.json
├── assets/
│   ├── icon.png         # tomato icon (generated via QPainter)
│   ├── alarm.wav        # 3-beep ascending tone
│   ├── bell.wav         # resonant bell
│   ├── digital.wav      # retro double-beep bursts
│   └── soft.wav         # gentle two-tone chime
└── requirements.txt
```

## Architecture

**Signal flow:** `timer.py` is the only source of truth — emits `tick(int)`, `phase_started(str)`, `phase_ended(str)`, `paused()`, `resumed()`, `stopped()`. All other modules listen; none call each other directly.

**State machine:**
```
IDLE → WORK → BREAK → IDLE   (break end does NOT auto-start work)
Any active state → PAUSED → resume back to same phase
Any active/paused state → STOPPED → IDLE
```

**Tray icon:** Static tomato when idle; red dot during work, green dot during break. Context menu shows live `mm:ss` countdown (updated every tick via signal). Opening the menu always shows the current remaining time.

**Minimize / close:** Both hide the window to tray (`changeEvent` + `closeEvent` override). `app.setQuitOnLastWindowClosed(False)` keeps the process alive. Quit only via tray → Quit.

**Config** persists to `~/.config/pomodoro/config.json`. First launch seeds the sounds dir and copies all four bundled `.wav` files.

**Stats** persists to `~/.config/pomodoro/pomodoro.db` (SQLite). One row per work session with `started_at` (when work began) and `completed_at` (when it finished; NULL if stopped early). `stats.begin_session()` is called on `phase_started("work")`; `stats.record_session()` is called on `phase_ended("work")`. Historical `stats.json` is migrated on first launch and renamed to `stats.json.bak`. The Stats tab reads `stats.last_7_days()` to render a bar chart.

**Colors:** work = `#D85A30`, break = `#1D9E75`, stop button = `#C0392B`.

## Config schema

```json
{
  "work_duration": 25,
  "break_duration": 5,
  "long_break_duration": 15,
  "pomodoros_until_long_break": 4,
  "volume": 80,
  "selected_sound": "~/.config/pomodoro/sounds/default.wav",
  "repeat_interval": 30,
  "auto_start_break": true,
  "daily_goal": 0
}
```

## Stats schema (SQLite — `~/.config/pomodoro/pomodoro.db`)

```sql
CREATE TABLE sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    date         TEXT NOT NULL,      -- ISO-8601 date, e.g. '2026-06-19'
    started_at   TEXT NOT NULL,      -- UTC datetime, e.g. '2026-06-19T14:00:00'
    completed_at TEXT                -- NULL if session was stopped early
);
```

## Known behaviour

- `QSystemTrayIcon.activated` does not fire on GNOME — all tray clicks open the context menu. Time display lives in the menu itself.
- `QSystemTrayIcon.showMessage` is unreliable on GNOME — use `notify-send` for all notifications.
- `libxcb-cursor0` must be installed (`sudo apt install libxcb-cursor0`) for PyQt6 xcb platform plugin to load.
- Tray dot icons are created inside `TrayIcon.__init__` (not at module level) because `QPixmap` requires a `QGuiApplication` to exist first.
