# Review and improvement priorities

## Implemented in this update

| Change | Result |
| --- | --- |
| SQLite database | Garmin summaries, extra endpoint responses, workbook imports and manual logs are collected locally. Stable record keys prevent repeat-import duplicates; failed imports roll back. |
| Local logging | Meals, workouts and check-ins persist in SQLite. The JSON export remains compatible with the earlier version. |
| Reference-based interface | Full-page photographic background, translucent panels, warm accent, compact navigation, summary cards, a calendar and expandable forms. |
| Better recovery view | A real per-activity load sum replaces the former sleep-goal card; missing load is visible. Sleep, HRV, resting HR, stress and Body Battery remain separate. |
| Twice-daily sync | Scheduled at 08:00 and 22:00 Mac local time. Refreshes extra endpoints, recent data, missed days and failed historical health batches. Older successful extra data is cached. |
| Preservation and backup | Failed health requests retain earlier values. Successful downloads replace only their date range. A dated SQLite backup is generated with the personal build. |
| Public demo | An explicit publishing allowlist exports code and fictional data. Personal profiles, calendars, workbooks, health records, logs and credentials stay local. |
| Deployment | GitHub Actions runs tests, rebuilds the fictional demo and publishes it to Pages on a main-branch push. |

## Best next improvements

| Priority | Improvement | Why it helps | Automation and limits |
| --- | --- | --- | --- |
| 1 | Visible sync age and freshness reminders | Makes it clear when the morning or evening sync missed new watch data. | The installer now includes both 08:00 and 22:00 triggers. Sync still depends on Mac power, login and Garmin availability. |
| 1 | Edit an existing meal, save recipes and export logs | Faster logging and corrections; avoids adding a second entry for a corrected portion. | Ingredient presets and repeated meals can be automated. Oil, cooked weight and the amount eaten still need confirmation. Current version supports adding/removing and planned/eaten status. |
| 1 | Morning-weight trend and complete-day flag | A seven-day average is more useful than morning-to-evening variation. A partial food log should not imply a deficit. | Compute averages only from morning readings, label missing days and compare two complete weeks. Mark complete food days explicitly. |
| 1 | Weekly review of planned versus completed work | Shows consistency, running volume, intensity and strength progress together. | Auto-generate a summary from the calendar, Garmin and manual logs. Review fatigue, pain and schedule changes yourself. |
| 2 | Editable calendar and structured workout steps | Makes changes easier without updating Excel or a local JSON file. | Add session editing, warm-up/work/cool-down blocks and calendar export. Garmin watch write-back requires separately supported official endpoints. |
| 2 | Recovery context | HRV baseline, resting-HR change, sleep consistency and subjective fatigue are easier to interpret together. | Show dated trends and the reasons for an easy/rest suggestion. Avoid invented readiness scores or automatic medical conclusions. |
| 2 | Backup retention, export and restore check | A backup on the same disk does not protect against losing the disk. | Retain several daily/weekly versions, verify restore and support encrypted off-device backup. Requires a chosen destination. |
| 2 | Short sync-failure notification | Discover expired credentials or missed updates without reading logs. | A local notification can report failure count and last successful sync; no health details need to leave the Mac. |
| 3 | Protected access from a phone | Lets the same real dashboard work away from the Mac. | Needs authenticated hosting, encrypted storage, controlled API access and deployment design. GitHub Pages alone is static and public. |
| 3 | Deeper sport analysis | Running power/cadence/HR zones, cycling power and sleep stages can answer specific training questions. | Implement only where the device returns enough useful values; avoid filling the page with empty cards. |
| 3 | External AI, if wanted | More flexible questions and weekly explanations. | The current helper is local rules. Adding an external model would require choosing what private data may be sent, a provider and a cost limit. |

## Keep the interface simple

Keep four summary cards, one recommendation and the next key session in the default view. Put detailed charts and records inside History, the entry forms inside their respective workspaces, and evidence behind “Why this?”. Display measurement dates and missing readings clearly. Add a new metric only if it changes a training decision.

## Things that still need your judgment

Sleep, HRV and estimated energy expenditure do not fully describe recovery. Pain, illness, unusual fatigue, appetite, schedule and whether a food log is complete need your input. Training and food targets should be adjusted with sustained trends and performance, not one weigh-in or one watch estimate.

The existing workbook can contain distances that exceed recent training. An imported session is a plan to review, not an instruction to complete at all costs. Calendar overrides take priority.
