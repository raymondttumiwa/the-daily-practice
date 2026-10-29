# Garmin data and display coverage

The official Personal API's documented fields and your account's returned values are different things. A watch must support and record a metric before a useful reading can appear. The dashboard's **Available data & sync details** counts non-null positive readings from actual downloads.

## Shown now

| Area | Data displayed |
| --- | --- |
| Activities | All downloaded sports, monthly training hours by sport, weekly totals, distance, duration, elevation, average/max HR, aerobic/anaerobic effect, estimated calories and per-activity training load. |
| Records | Longest run and ride by distance, longest session by timer duration, largest training day by summed duration. |
| Load | Rolling seven-day sum of Garmin per-activity load, filtered by sport; incomplete windows stay unavailable. |
| Recovery | Sleep duration and score, overnight and weekly HRV, resting HR, Body Battery peak, stress. |
| More health | Steps, respiration, SpO₂, estimated total calories burned and fitness age where returned. |
| Coaching | Imported session, actual recorded activities, dated recovery evidence, fatigue/soreness/pain check-in and a conservative session recommendation. |
| Food | Eaten/planned entries, daily calories/protein/carbs, label-based presets and flags for unquantified ingredients. |

HRV and Body Battery are not converted into a made-up training-readiness score. The saved official API specification exposes no daily readiness endpoint. The load graph is a simple rolling sum, not Garmin's weighted acute load.

## Stored but only partly displayed

Extra responses are kept in private SQLite records and `data/garmin/extended/`. The website only embeds selected fields.

| Category | Candidate next views, when supported |
| --- | --- |
| Running | Cadence, stride length, ground contact, vertical oscillation/ratio, grade-adjusted pace, power, HR-zone time and fastest splits. |
| Cycling | Cadence, average/max/normalized power, sustained power, FTP and time in power zones. |
| Swimming | Stroke metrics, SWOLF, pool lengths and recorded distance. |
| Strength | Recorded sets, repetitions and structured workout steps. |
| Sleep | Stage breakdown, timing consistency, naps, sleep need, breathing disruption, sleep stress and sleep HR. |
| HRV and heart rate | Detailed overnight series, five-minute high, baseline and daily HR series. |
| Daily wellness | Steps/goals, intensity minutes, hydration, Body Battery charge/drain and stress reports. |
| Fitness | VO₂ max, lactate threshold, activity impact load, training stress score and intensity factor. |
| Body and nutrition | Weight and composition where returned by supported hardware; Garmin meal/nutrition logs if used. Local food logs remain separate. |

Original FIT/GPX files and route coordinates are not downloaded. Identity, location and free-text fields are removed from extra responses. A schema field being documented does not prove it exists in your account.

## Sync behavior

`python3 scripts/sync_history.py` includes extra metrics, caches older successful detail downloads, refreshes the recent seven days and retries transient failures. The same command is scheduled at 08:00 and 22:00 daily, Mac local time. `--full` requests a complete refresh. `python3 scripts/sync_available.py --force` forces only the expanded collection.

Failures are listed in the history page and `extended/manifest.json`. Previously downloaded data is retained on request failures; successful empty responses remain empty. Older 400/403/404 responses are cached until a forced request. Network failures and missing device data cannot be fixed by estimating a value.

The saved machine-readable catalog is `docs/garmin-api-catalog.json`. Official reference: https://developer.garmin.com/gc-developer-program/personal/swagger-docs/
