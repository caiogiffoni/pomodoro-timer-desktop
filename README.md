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
- Post-session review: log what you worked on, tag it, and rate your focus (1–5)
- Review dialog auto-fills from the previous session of the day — edit or clear as needed
- Break alarm auto-stops after a configurable timeout (default 3 min; set to 0 to disable)
- Config persists to `~/.config/pomodoro/config.json`
- Session stats tracked in `~/.config/pomodoro/pomodoro.db` (SQLite)

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

Each work session is recorded in `~/.config/pomodoro/pomodoro.db` (SQLite). Completed sessions store:

- `started_at` / `completed_at` — UTC timestamps
- `planned_duration_seconds` — work duration at the time
- `pomodoro_number` — position in the current cycle (1–4)
- `day_session_index` — nth session of the day
- `notes`, `tag`, `focus_score` — from the optional post-session review dialog

Sessions stopped early are kept with `completed_at = NULL` and excluded from counts. Existing `stats.json` data is migrated automatically on first launch.

The Stats tab shows a 7-day bar chart and full history list. The tray context menu shows today's count.

## Testing

```bash
uv run pytest
```

CI runs automatically on every push via `.github/workflows/test.yml`.
