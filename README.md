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
- Dashboard tab: summary cards, project/tag breakdowns, and start-hour histogram over 7D / 30D / All
- Projects tab: create and activate projects — sessions started with an active project are linked to it; archiving hides a project but keeps its history
- Streak tracking and daily goal progress
- Post-session review: pick a project, log what you worked on, tag it, and rate your focus (1–5)
- Review dialog auto-fills from the active project and the previous session — edit or clear as needed
- Break alarm auto-stops after a configurable timeout (default 3 min; set to 0 to disable)
- Config persists to `~/.config/pomodoro/config.json`
- Session stats tracked in `~/.config/pomodoro/pomodoro.db` (SQLite)

## Pomodoro behavior

The timer follows the classic pomodoro cycle:

1. **Work** (default 25 min) — press Start to begin. Completing a work session counts as one pomodoro.
2. **Break** (default 5 min) — follows each work session. Every 4th pomodoro (configurable via `pomodoros_until_long_break`) earns a **long break** (default 15 min) instead.
3. Back to idle — when a break ends, the next work session is **never** auto-started; you may be away from the keyboard, so work always requires a manual Start.

Breaks can start automatically after work ends (`auto_start_break`, on by default) or wait for you to start them. The alarm sound repeats every `repeat_interval` seconds until acknowledged, and a break alarm gives up on its own after a configurable timeout (default 3 min).

**Pause/Resume** freezes the current phase and picks it back up where it left off. **Stop** aborts the phase and returns to idle — a stopped work session is recorded but never counts toward stats, streaks, or the daily goal.

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
  "long_break_duration": 15,
  "pomodoros_until_long_break": 4,
  "volume": 80,
  "selected_sound": "~/.config/pomodoro/sounds/default.wav",
  "repeat_interval": 30,
  "auto_start_break": true,
  "daily_goal": 0,
  "active_project_id": 1
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
- `project_id` — the active project at session start (or the one picked in the review dialog)

Projects live in their own `projects` table. Activating a project in the Projects tab links every new work session to it; the review dialog can override or clear the link afterwards. Archiving removes a project from the list without touching its session history.

Sessions stopped early are kept with `completed_at = NULL` and excluded from counts. Existing `stats.json` data is migrated automatically on first launch.

The Stats tab shows a 7-day bar chart and full history list, the Dashboard tab aggregates completed sessions (summary cards, top-5 project and tag bars, start-hour histogram) over a selectable period, and the tray context menu shows today's count.

## Testing

```bash
uv run pytest
```

CI runs automatically on every push via `.github/workflows/test.yml`.
