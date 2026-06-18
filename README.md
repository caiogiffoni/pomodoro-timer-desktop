# pomodoro-timer-desktop

A Pomodoro timer desktop app for Ubuntu (Linux) built with Python + PyQt6.

## Features

- Circular arc countdown drawn with QPainter, depletes clockwise
- Work phase (default 25 min) — red-orange arc; break phase (default 5 min) — teal arc
- Start, Pause/Resume, and Stop controls
- Optional auto-start break; work always requires manual start (you may be away)
- System tray icon: red dot during work, green dot during break, tomato when idle
- Tray context menu shows live countdown (`mm:ss`) and today's session count
- Desktop notification + alarm sound on phase end
- Minimize or close sends the window to tray; app keeps running until Quit
- Settings dialog: durations, volume, sound picker, auto-start break, daily goal
- 4 bundled alarm sounds: default beeps, bell, digital, soft chime
- Stats tab: 7-day bar chart with week navigation + scrollable full history list
- Streak tracking and daily goal progress
- Config persists to `~/.config/pomodoro/config.json`
- Daily session stats tracked in `~/.config/pomodoro/stats.json`

## Requirements

- Ubuntu 24.04
- `notify-send` (pre-installed on Ubuntu)
- `uv` — install once: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Setup

```bash
git clone <repo> && cd pomodoro-timer-desktop
./setup.sh
```

`setup.sh` installs `libxcb-cursor0` via apt, installs `uv` if missing, runs `uv sync`
to get Python 3.14 + PyQt6, and creates a `pomodoro` launcher in `~/.local/bin/`.

After that, just run:

```bash
pomodoro
# or
uv run python main.py
```

## Config

Created automatically at `~/.config/pomodoro/config.json` on first launch.

```json
{
  "work_duration": 25,
  "break_duration": 5,
  "volume": 80,
  "selected_sound": "~/.config/pomodoro/sounds/default.wav"
}
```

Bundled sounds are copied to `~/.config/pomodoro/sounds/` on first launch and are selectable from Settings.

## Stats

Each completed work session is recorded in `~/.config/pomodoro/stats.json`, keyed by ISO date:

```json
{
  "2026-06-18": 3,
  "2026-06-17": 1
}
```

The Stats tab in the main window shows a bar chart of the last 7 days. The tray context menu shows today's count.
