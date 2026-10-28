# Local Garmin setup

## Launch your personal desk

```bash
python3 scripts/coach_server.py
```

Open http://127.0.0.1:8765 and keep Terminal running while saving. Stop with Ctrl+C. Restart after changing server code. Opening `outputs/garmin-dashboard/index.html` directly gives a readable snapshot; use the server to save entries to SQLite.

The page combines an imported calendar, workout guidance, a timer, food logging, check-ins and Garmin history. Planned meals are excluded until marked eaten. Manual exercise logs stay separate from Garmin totals to avoid double counting. The question helper answers with local rules, not an external language model.

## Settings and imports

Store your API key in `.env.local`, using `.env.example` as the template. Tokens remain in memory. Never paste credentials into a public repository or website.

The following optional local files provide personal information:

- `data/coach/profile.json`: display name, race date, protein target and optional calendar start.
- `data/coach/calendar_overrides.json`: an array of sessions that take priority over the workbook.
- `Marathon_Plan.xlsx`: existing `Training Plan`, `Calendar` and `Strength (No Gym)` sheets.
- `outputs/calorie-tracker/Daily_Calorie_Tracker.xlsx`: existing food and weight records.

Example profile (replace with your own settings):

```json
{"name":"Runner","raceDate":"2027-04-18","proteinTarget":150,"calendarStart":"2026-09-14"}
```

Example override:

```json
[{"date":"2027-01-09","title":"Long Run","km":12,"description":"Conversational effort.","source":"Personal plan"}]
```

Workbook import uses this project's existing sheet layout. It is not a general-purpose Excel importer. Original workbooks are read without modification; cached formula values must already be saved in Excel. Missing source workbooks are allowed.

## Refresh data

```bash
python3 scripts/sync_history.py
```

Activities are scanned from June 1, 2026 through today in Asia/Shanghai. Recovery refreshes the recent seven days, any missed period since the previous sync, and earlier failed batches. Extra account, activity and wellness endpoints are included. Older successful extra downloads are cached. Older HTTP 400/403/404 failures are shown in the manifest and retried only on a forced refresh.

```bash
# Recheck all old health periods and extra endpoints:
python3 scripts/sync_history.py --full
# Quick refresh of activity and recovery summaries only:
python3 scripts/sync_history.py --no-extended
# Rebuild from local records without Garmin:
python3 scripts/build_dashboard.py
```

A successful empty response means Garmin returned no records for that range; it does not mean zero sleep or HRV. A failed request preserves earlier readings and remains listed in the page's data details. Activity pagination must complete before the downloaded activity range is replaced. Multisport child legs are excluded to avoid adding both a parent session and its legs.

Standalone expanded sync is available as `python3 scripts/sync_available.py`; it also rebuilds the page. `--force` rechecks its cached older responses.

## macOS schedule

```bash
python3 scripts/install_daily_sync.py
launchctl print gui/$(id -u)/com.raymond.garmin-sync
```

The LaunchAgent runs immediately on installation and daily at 22:00 Mac local time. It persists across restarts. If the Mac is asleep at the scheduled time, launchd normally runs the missed job after waking; it cannot fetch data while powered off, logged out or offline. Garmin must receive your watch data first. An expired API key must be replaced locally.

The installed job invokes `scripts/sync_history.py`, so updates to that script are used without reinstalling the schedule. Moving this project or changing the desired time requires reinstalling it.

Progress appears in `logs/garmin-sync.log`; errors in `logs/garmin-sync-error.log`. The nightly build backs up SQLite to `data/backups/training-YYYY-MM-DD.sqlite3`. This is a same-disk recovery copy, not an off-device backup. Keep an encrypted external backup for protection against a lost disk.

## Data and presentation

History includes monthly hours by sport, weekly totals, longest run and ride, longest session and biggest day, per-activity load, sleep, HRV, resting heart rate, stress and Body Battery. Date and sport filters apply to training; recovery follows the date filter.

The load chart sums Garmin per-activity training load over seven days. It is not Garmin's weighted acute-load calculation. Missing load values make a window incomplete. No training-readiness score is supplied by the saved official API specification, so none is fabricated.

The app binds only to localhost. Requests that save entries must come from the local page. Personal data is not sent to GitHub Pages. See [data availability](docs/GARMIN-DATA.md) and [improvements](docs/ROADMAP.md).

Official reference: https://developer.garmin.com/gc-developer-program/personal/swagger-docs/
