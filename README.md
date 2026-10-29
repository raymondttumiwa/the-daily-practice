# The Daily Practice

[Live demo](https://raymondttumiwa.github.io/the-daily-practice/) · [GitHub repository](https://github.com/raymondttumiwa/the-daily-practice)

A simple training desk for workouts, recovery, meals and a calendar. Python builds a standalone page; no JavaScript framework, package installation, or external AI service is required.

The interface uses a full-page photographic background, translucent panels, restrained orange accents and expandable workspaces. Your daily session and four summary cards stay visible; detailed logs and history open when needed.

## Try the demo

```bash
python3 scripts/build_dashboard.py --demo
python3 -m http.server 8000 --directory site
```

Open http://localhost:8000. The demo uses generated fictional data. Food, workouts and check-ins entered there are saved only in that browser's local storage. They are not sent to Garmin, GitHub or your personal database.

## Use your own data locally

```bash
cp .env.example .env.local
# Set your Garmin Personal API key in .env.local using your editor.
python3 scripts/sync_history.py
python3 scripts/coach_server.py
```

Open http://127.0.0.1:8765. Keep the server running while saving entries. No credentials are embedded in the dashboard.

Your SQLite database is `data/training.sqlite3`. Garmin downloads and existing workbook sources are retained. New meals, manual sessions and check-ins save to SQLite, with a JSON compatibility export. Existing supported plan and food workbooks are optional; they are imported when present.

Personal settings belong in the ignored `data/coach/profile.json`, and calendar changes in `data/coach/calendar_overrides.json`. See [local setup](README-Garmin.md), [file guide](FILES.md) and [available Garmin data](docs/GARMIN-DATA.md).

## Daily automation

```bash
python3 scripts/install_daily_sync.py
```

On macOS, this installs a daily sync at 22:00 Mac local time. It refreshes activities, catches up after offline days, refreshes recent recovery and extra metrics, imports the database, creates a daily backup and rebuilds your personal page. Older successful detail downloads are reused. Failed requests are reported; earlier readings are retained on failure.

The Mac must be logged in with network access, and your watch must have synced with Garmin. Refresh the page to see a completed sync. This local schedule does not upload your personal records.

## GitHub Pages

The included workflow tests the code, builds a **fictional demo** and deploys `site/`. In the repository's **Settings → Pages**, select **GitHub Actions** as the source. Push to `main` or run the workflow manually.

GitHub Pages runs a static demo. Your personal server and private database continue to run on your Mac. Hosting real records with logging would need a separate authenticated backend.

`data/`, `.env.local`, workbooks, personal outputs, logs, backups and reference PDFs are excluded from the publishing bundle. Generate a clean bundle with:

```bash
python3 scripts/prepare_publish.py --destination /private/tmp/daily-practice-publish
```

## Validation

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_dashboard.py --demo
node tests/dashboard.mjs site/index.html
```

[Implemented features and improvement priorities](docs/ROADMAP.md). Recommendations use local rules and recorded evidence. Missing readings remain unavailable; the page does not invent Garmin training readiness.
