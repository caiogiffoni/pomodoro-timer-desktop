# pomodoro-timer-desktop

A Pomodoro timer desktop app for Ubuntu (Linux) built with Python + PyQt6.

## Features

- Circular arc countdown drawn with QPainter, depletes clockwise
- Work phase (default 25 min) — red-orange arc; break phase (default 5 min) — teal arc
- Start, Pause/Resume, and Stop controls
- Break starts automatically when work ends; work requires manual start (you may be away)
- System tray icon: red dot during work, green dot during break, tomato when idle
- Tray context menu shows live countdown (`mm:ss`) that updates in real time
- Desktop notification + alarm sound on phase end
- Minimize or close sends the window to tray; app keeps running until Quit
- Settings dialog: work/break durations, volume slider, sound file picker
- 4 bundled alarm sounds: default beeps, bell, digital, soft chime
- Config persists to `~/.config/pomodoro/config.json`

## Requirements

- Ubuntu 24.04
- Python 3.14
- `libxcb-cursor0`: `sudo apt install libxcb-cursor0`
- `notify-send` (pre-installed on Ubuntu)

## Setup

```bash
git clone <repo> && cd pomodoro-timer-desktop
uv pip install PyQt6
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
