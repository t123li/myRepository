# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run

```bash
python pomodoro.py
```

Zero dependencies beyond Python standard library (tkinter, winsound).

## Architecture

Single-file tkinter desktop app: `PomodoroTimer` class in `pomodoro.py`.

### Timer state machine

Three modes cycled automatically: `work` (25 min) → `short_break` (5 min) / `long_break` (15 min) → `work` ...
Every 4th completed work session triggers a long break instead of a short break.

Timing is driven by `window.after(1000, self._tick)` — a tkinter callback that fires every second. There is no background thread.

### Key instance state

| Field | Purpose |
|-------|---------|
| `mode` | `"work"`, `"short_break"`, or `"long_break"` |
| `time_left` / `total_time` | seconds remaining and total for the current phase |
| `completed` | count of finished work sessions (never reset, drives break selection and labels) |
| `running` | whether the timer is actively counting down |
| `timer_id` | handle from `window.after()`; non-None means a tick is scheduled |

### Call flow

- User clicks "开始/暂停" → `_on_start_pause()` → `start()` or `pause()`
- Each second → `_tick()` decrements `time_left`, calls `_update_display()` → `_draw()`
- When `time_left` hits 0 → `_notify()` (winsound beep + focus window), then `_switch_mode()`
- `skip()` also calls `_switch_mode()` without waiting for the timer to expire

### Platform note

`winsound` is Windows-only. On macOS/Linux the import at line 2 will crash. To make it cross-platform, guard the import and provide a fallback notification (e.g., `print("\a")` or `tkinter` bell).
