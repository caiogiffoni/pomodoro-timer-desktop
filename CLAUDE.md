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
# Install dependencies
uv pip install PyQt6

# Run
uv run python main.py
```

## Structure

```
├── main.py              # boot: seeds config, wires all modules
├── app/
│   ├── timer.py         # QTimer state machine — no UI imports
│   ├── window.py        # MainWindow + QPainter arc
│   ├── tray.py          # QSystemTrayIcon + context menu
│   ├── notifier.py      # QMediaPlayer + notify-send
│   ├── settings.py      # QDialog: durations, volume, sound picker
│   └── config.py        # load/save ~/.config/pomodoro/config.json
├── assets/
│   ├── icon.png         # tomato icon (generated via QPainter)
│   ├── alarm.wav        # 3-beep ascending tone
│   ├── bell.wav         # resonant bell
│   ├── digital.wav      # retro double-beep bursts
│   └── soft.wav         # gentle two-tone chime
└── requirements.txt
```

## Architecture

**Signal flow:** `timer.py` is the only source of truth — emits `tick(int)`, `phase_ended(str)`, `paused()`, `resumed()`, `stopped()`. All other modules listen; none call each other directly.

**State machine:**
```
IDLE → WORK → BREAK → IDLE   (break end does NOT auto-start work)
Any active state → PAUSED → resume back to same phase
Any active/paused state → STOPPED → IDLE
```

**Tray icon:** Static tomato when idle; red dot during work, green dot during break. Context menu shows live `mm:ss` countdown (updated every tick via signal). Opening the menu always shows the current remaining time.

**Minimize / close:** Both hide the window to tray (`changeEvent` + `closeEvent` override). `app.setQuitOnLastWindowClosed(False)` keeps the process alive. Quit only via tray → Quit.

**Config** persists to `~/.config/pomodoro/config.json`. First launch seeds the sounds dir and copies all four bundled `.wav` files.

**Colors:** work = `#D85A30`, break = `#1D9E75`, stop button = `#C0392B`.

## Config schema

```json
{
  "work_duration": 25,
  "break_duration": 5,
  "volume": 80,
  "selected_sound": "~/.config/pomodoro/sounds/default.wav"
}
```

## Known behaviour

- `QSystemTrayIcon.activated` does not fire on GNOME — all tray clicks open the context menu. Time display lives in the menu itself.
- `QSystemTrayIcon.showMessage` is unreliable on GNOME — use `notify-send` for all notifications.
- `libxcb-cursor0` must be installed (`sudo apt install libxcb-cursor0`) for PyQt6 xcb platform plugin to load.
- Tray dot icons are created inside `TrayIcon.__init__` (not at module level) because `QPixmap` requires a `QGuiApplication` to exist first.
