# pomodoro-timer-desktop

A Pomodoro timer desktop app for Ubuntu (Linux) built with Python + PyQt6.

## Features

- Circular arc countdown drawn with QPainter (depletes clockwise)
- Work phase: 25 min, red arc (`#D85A30`)
- Break phase: 5 min, teal arc (`#1D9E75`)
- System tray icon with tooltip (remaining time) and context menu
- Desktop notification + alarm sound on phase end
- Settings dialog: durations, volume, sound file picker

## Requirements

- Ubuntu 24.04
- Python 3.14
- `notify-send` (usually pre-installed on Ubuntu)

## Setup

```bash
# Clone and enter
git clone <repo> && cd pomodoro-timer-desktop

# Install dependencies via uv
uv pip install PyQt6

# Run
uv run python main.py
```

## Config

Persisted to `~/.config/pomodoro/config.json`. Created automatically on first launch.

```json
{
  "work_duration": 25,
  "break_duration": 5,
  "volume": 80,
  "selected_sound": "~/.config/pomodoro/sounds/default.wav"
}
```

## Development

See `CLAUDE.md` for architecture details and the incremental build plan.
