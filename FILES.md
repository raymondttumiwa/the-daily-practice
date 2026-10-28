# File guide

Keep the active project together. Edit source files, then rebuild; edits to generated HTML will be overwritten.

| Keep | Purpose |
| --- | --- |
| `.env.local` | Private Garmin API key and download directory. Never publish. |
| `data/training.sqlite3` | Authoritative local database for imported records and new logs. Back up. |
| `data/coach/profile.json`, `calendar_overrides.json` | Private personal settings and calendar adjustments. |
| `data/coach/journal.json` | Compatibility export of manual logs; first imported when the database is created. SQLite takes priority afterward. |
| `data/garmin/history.json` | Latest downloaded activity and recovery summaries; input to database refresh. |
| `data/garmin/extended/` | Raw extra responses and request manifest; private. Selected fields enter the dashboard. |
| `Marathon_Plan.xlsx` | Existing plan, calendar and strength source, when used. |
| `outputs/calorie-tracker/Daily_Calorie_Tracker.xlsx` | Existing food and weight source, when used. |
| `scripts/coach_server.py` | Start the personal page and save logs. |
| `scripts/sync_history.py` | Main scheduled sync; also refreshes extended metrics and rebuilds the page. |
| `scripts/sync_available.py`, `sync_garmin.py` | Shared extra-endpoint sync and official API client. |
| `scripts/training_store.py`, `coach_data.py` | Database, backups and workbook imports. |
| `scripts/build_dashboard.py`, `coach_ui.py`, `history_dashboard.py`, `demo_data.py` | Build private HTML or a fictional demo. |
| `assets/desk.html`, `history.html`, `coach.js`, `history.js`, `dashboard.css` | Editable page templates, interactions and styling. |
| `references/Background.jpg` | Active background, embedded in the page at build time. |
| `scripts/install_daily_sync.py` | Install or repair the local schedule. |
| `scripts/prepare_publish.py` | Create a clean code and fictional-demo bundle for GitHub. |
| `tests/`, `.github/workflows/pages.yml` | Validation and automated demo deployment. |

## Generated and rebuildable

- `outputs/garmin-dashboard/index.html`: personal snapshot, recreated by the builder.
- `site/index.html`: fictional public demo, recreated with `--demo`.
- `data/backups/`: daily database recovery copies; retain several before cleanup.
- `logs/`: sync history useful for diagnosing issues.
- `scripts/__pycache__/`, `tests/__pycache__/`: automatic Python caches.
- `scripts/com.raymond.garmin-sync.plist`: generated schedule configuration. The installed copy is in `~/Library/LaunchAgents/`.
- `.garmin-sync.lock`: prevents overlapping main syncs; leave it in place.

## Optional references and older material

`archive/`, unused reference designs, reference PDFs, `Calories_Alienergy.jpg`, `assets/training-hero.jpg`, the initial `activity_sample.json` and `scripts/check_garmin.py` are not needed for normal daily use. Retain the food label if you want to recheck its nutrition values. No original food, plan or reference files were deleted.

`README.md` provides everyday commands. `README-Garmin.md` covers setup and scheduling. `docs/GARMIN-DATA.md` describes returned data; `docs/ROADMAP.md` lists improvement priorities.

## What gets published

Only the explicit allowlist in `scripts/prepare_publish.py`: code, tests, general documentation, the active background and fictional demo. No private database, profile, calendar, source workbooks, food label, health downloads, logs or personal HTML is included. The runtime also ignores those locations in Git.
