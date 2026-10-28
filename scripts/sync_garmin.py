"""Download a small activity sample using Garmin's official Personal API.

Only training summary fields are saved; credentials stay in memory.
Docs: https://developer.garmin.com/gc-developer-program/personal/swagger-docs/
"""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://personal.connectapi.garmin.com'


def request(path, authorization, method='GET'):
    req = urllib.request.Request(
        BASE + path,
        data=b'' if method == 'POST' else None,
        headers={'Authorization': authorization},
        method=method,
    )
    # Refuse redirects so authorization cannot be forwarded to another host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as response:
        return response.read().decode('utf-8').strip()


def main():
    settings = {}
    for line in (ROOT / '.env.local').read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            name, value = line.split('=', 1)
            settings[name.strip()] = value.strip().strip('"').strip("'")
    key = settings.get('GARMIN_PERSONAL_API_KEY', '')
    if not key or any(c in key for c in '\r\n'):
        raise SystemExit('Missing or invalid GARMIN_PERSONAL_API_KEY.')
    raw = request('/personalapitoken-service/personal-api/personal-api-key/token',
                  'ApiKey ' + key, 'POST')
    try:
        token = json.loads(raw)
    except json.JSONDecodeError:
        token = raw
    if isinstance(token, dict):
        token = token.get('access_token') or token.get('accessToken') or token.get('token')
    if not isinstance(token, str) or not token or any(c.isspace() for c in token) or '<' in token:
        raise SystemExit('Unrecognized token response; body withheld.')
    raw = request('/activitylist-service/activities/search/activities?start=0&limit=5&sortOrder=desc',
                  'Bearer ' + token)
    try:
        activities = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit('Activities endpoint returned non-JSON content; body withheld.') from None
    if not isinstance(activities, list) or not all(isinstance(a, dict) for a in activities):
        raise SystemExit('Unexpected activities response; body withheld.')
    fields = ('activityId', 'startTimeLocal', 'distance', 'duration', 'movingDuration',
              'elapsedDuration', 'averageHR', 'maxHR', 'averageSpeed', 'elevationGain',
              'calories', 'aerobicTrainingEffect', 'anaerobicTrainingEffect')
    summaries = []
    for activity in activities:
        summary = {field: activity[field] for field in fields if field in activity}
        kind = activity.get('activityType')
        if isinstance(kind, dict):
            summary['activityType'] = kind.get('typeKey')
        summaries.append(summary)
    directory = ROOT / settings.get('GARMIN_DATA_DIR', './data/garmin')
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / 'activity_sample.json'
    content = json.dumps(summaries, indent=2) + '\n'
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as file:
        file.write(content)
    os.chmod(destination, 0o600)
    print(f'Garmin API access verified. Downloaded {len(summaries)} activity summaries.')
    print('Saved to:', destination)
    print('No tokens, route coordinates or activity names were saved.')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'Garmin returned HTTP {error.code}; response body withheld.') from None
    except urllib.error.URLError:
        raise SystemExit('Cannot reach Garmin. Check DNS/network access.') from None
    except (TimeoutError, OSError):
        raise SystemExit('Network or local file operation failed; check connectivity and file permissions.') from None
