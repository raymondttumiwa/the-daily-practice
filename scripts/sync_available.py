"""Fetch extended documented Garmin data; preserve ordinary dashboard history separately."""
import argparse
import fcntl
import http.client
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import urllib.error
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import sync_garmin as api
from sync_history import get_json, save

ROOT = Path(__file__).resolve().parents[1]


def clean(value):
    """Exclude identity, free text and location fields from extra training records."""
    if isinstance(value, list):
        return [clean(x) for x in value]
    if isinstance(value, dict):
        blocked = ('latitude', 'longitude', 'position', 'coordinate', 'polyline', 'email',
                   'username', 'displayname', 'fullname', 'profileimage', 'userprofile',
                   'owner', 'address', 'description', 'comment', 'note', 'image', 'media', 'uuid')
        return {k: clean(v) for k, v in value.items()
                if not any(word in k.lower() for word in blocked)
                and k.lower() not in ('name', 'activityname', 'locationname', 'userid', 'profileid')}
    return value


def run(start, end, token, directory, force=False):
    """Refresh seven recent days and new activities; reuse older successful downloads."""
    refresh_from = end - timedelta(days=6)
    folder = directory / 'extended'
    folder.mkdir(parents=True, exist_ok=True)
    old_manifest = folder / 'manifest.json'
    previous = json.loads(old_manifest.read_text()).get('requests', []) if old_manifest.exists() else []
    previous = {r['series']: r for r in previous}
    manifest = {'start': start.isoformat(), 'end': end.isoformat(), 'updated': datetime.now().astimezone().isoformat(), 'requests': []}
    def fetch(label, path, cacheable=False):
        target = folder / (label + '.json')
        old = previous.get(label, {})
        if cacheable and not force and old.get('reason') in ('HTTP 400', 'HTTP 403', 'HTTP 404'):
            manifest['requests'].append({**old, 'cached': True})
            return
        if target.exists() and cacheable and not force:
            try:
                data = json.loads(target.read_text())
            except (ValueError, UnicodeDecodeError):
                pass  # Replace an unreadable cached response with a fresh download.
            else:
                manifest['requests'].append({'series': label, 'status': 'ok',
                                            'file': target.name, 'cached': True,
                                            'empty': data is None or data == [] or data == {}})
                save(folder / 'manifest.json', manifest)
                return
        try:
            data = clean(get_json(path, token))
            save(target, data)
            status = {'series': label, 'status': 'ok', 'file': target.name,
                      'empty': data is None or data == [] or data == {}}
        except urllib.error.HTTPError as e:
            status = {'series': label, 'status': 'failed', 'reason': f'HTTP {e.code}'}
        except (urllib.error.URLError, TimeoutError, ValueError,
                http.client.HTTPException, ConnectionError):
            status = {'series': label, 'status': 'failed', 'reason': 'Network or response error'}
        manifest['requests'].append(status)
        save(folder / 'manifest.json', manifest)
        print(label + ': ' + status['status'], flush=True)
    fetch('heart-rate-zones', '/biometric-service/heartRateZones/v2')
    fetch('user-settings', '/userprofile-service/userprofile/settings')
    current = start
    while current <= end:
        until = min(current + timedelta(days=6), end)
        a, b = current.isoformat(), until.isoformat()
        query = urlencode({'startDate': a, 'endDate': b})
        paths = {
            'hydration': f'/usersummary-service/stats/hydration/daily/{a}/{b}',
            'steps': f'/usersummary-service/stats/steps/daily/{a}/{b}',
            'stress': f'/usersummary-service/stats/stress/daily/{a}/{b}',
            'weight-all': f'/weight-service/weight/all/{a}/{b}',
            'weight-summary': f'/weight-service/weight/range/{a}/{b}',
            'weight-goals': f'/goal-service/goal/user/effective/weightgoal/{a}/{b}',
            'body-battery': '/wellness-service/wellness/bodyBattery/reports/daily?' + query,
            'wellness-activities': f'/wellnessactivity-service/activity/summary/range/{a}/{b}',
        }
        for kind, path in paths.items():
            fetch(f'{kind}-{a}-{b}', path, cacheable=until < refresh_from)
        current = until + timedelta(days=1)
    current = start
    while current <= end:
        d = current.isoformat()
        paths = {
            'fitness-age': f'/fitnessage-service/fitnessage/v2/{d}',
            'hrv-detail': f'/hrv-service/hrv/{d}',
            'nutrition': f'/nutrition-service/food/logs/{d}?includeGoals=true&includeNutrition=true&includeMedia=false',
            'sleep-detail': f'/sleep-service/sleep/dailySleep?date={d}',
            'daily-summary': f'/usersummary-service/usersummary/daily?calendarDate={d}',
            'spo2': f'/wellness-service/wellness/daily/spo2acclimation/{d}',
            'heart-rate-detail': f'/wellness-service/wellness/dailyHeartRate?date={d}',
        }
        for kind, path in paths.items():
            fetch(f'{kind}-{d}', path, cacheable=current < refresh_from)
        current += timedelta(days=1)
    history = directory / 'history.json'
    if history.exists():
        for activity in json.loads(history.read_text()).get('activities', []):
            if not start.isoformat() <= activity.get('startTimeLocal', '')[:10] <= end.isoformat():
                continue
            identity = activity['activityId']
            cacheable = activity.get('startTimeLocal', '')[:10] < refresh_from.isoformat()
            fetch(f'activity-{identity}', f'/activity-service/activity/{identity}', cacheable)
            fetch(f'workout-{identity}', f'/activity-service/activity/{identity}/workouts', cacheable)
    print('Extended data saved. Failed requests remain listed in extended/manifest.json.')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-06-01')
    parser.add_argument('--end', default=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat())
    parser.add_argument('--force', action='store_true', help='Refetch older cached responses and unsupported requests.')
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start:
        raise SystemExit('End precedes start.')
    settings = {}
    for line in (ROOT / '.env.local').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            settings[key.strip()] = value.strip().strip('"').strip("'")
    raw = api.request('/personalapitoken-service/personal-api/personal-api-key/token',
                      'ApiKey ' + settings['GARMIN_PERSONAL_API_KEY'], 'POST')
    try:
        decoded = json.loads(raw)
        token = decoded if isinstance(decoded, str) else decoded.get('access_token') or decoded.get('accessToken') or decoded.get('token')
    except json.JSONDecodeError:
        token = raw
    if not isinstance(token, str) or not token or any(c.isspace() for c in token) or '<' in token:
        raise SystemExit('Unexpected token response; withheld.')
    run(start, end, token, ROOT / settings.get('GARMIN_DATA_DIR', './data/garmin'), args.force)
    import build_dashboard
    build_dashboard.build()


if __name__ == '__main__':
    try:
        with (ROOT / '.garmin-sync.lock').open('w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SystemExit('A Garmin sync is already running.') from None
            main()
    except urllib.error.HTTPError as e:
        raise SystemExit(f'Garmin HTTP {e.code}; response withheld.') from None
    except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
        raise SystemExit('Cannot reach Garmin. Run this script from your Terminal.') from None
