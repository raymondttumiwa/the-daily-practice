"""Sync all Garmin activities and recovery summaries from June 1, 2026, then rebuild.

Uses documented Personal API endpoints only. Partial health failures are recorded
and shown in the dashboard. Tokens and location data are never persisted.
"""
import argparse
import fcntl
import http.client
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import time
import urllib.error
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import sync_garmin as api
import build_dashboard

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('activityId', 'startTimeLocal', 'startTimeGMT', 'activityType', 'eventType', 'isFavorite', 'isPR', 'isAutoCalcCalories', 'isParent', 'parentId', 'distance', 'duration', 'elapsedDuration', 'movingDuration', 'elevationGain', 'elevationLoss', 'averageSpeed', 'maxSpeed', 'calories', 'bmrCalories', 'averageHR', 'maxHR', 'averageRunningCadenceInStepsPerMinute', 'maxRunningCadenceInStepsPerMinute', 'maxLapAvgRunCadence', 'averageBikingCadenceInRevPerMinute', 'maxBikingCadenceInRevPerMinute', 'averageSwimCadenceInStrokesPerMinute', 'maxSwimCadenceInStrokesPerMinute', 'averageSwolf', 'activeLengths', 'steps', 'poolLength', 'unitOfPoolLength', 'beginTimestamp', 'sportTypeId', 'avgPower', 'maxPower', 'aerobicTrainingEffect', 'anaerobicTrainingEffect', 'strokes', 'normPower', 'leftBalance', 'rightBalance', 'avgLeftBalance', 'max20MinPower', 'avgVerticalOscillation', 'avgGroundContactTime', 'avgStrideLength', 'avgFractionalCadence', 'maxFractionalCadence', 'trainingStressScore', 'intensityFactor', 'vO2MaxValue', 'avgVerticalRatio', 'avgGroundContactBalance', 'lactateThresholdBpm', 'getlactateThresholdSpeed', 'maxFtp', 'avgStrokeDistance', 'avgStrokeCadence', 'maxStrokeCadence', 'avgStrokes', 'minStrokes', 'minTemperature', 'maxTemperature', 'minElevation', 'maxElevation', 'avgElevation', 'avgDoubleCadence', 'maxDoubleCadence', 'isElevationCorrected', 'summarizedExerciseSets', 'maxDepth', 'avgDepth', 'surfaceInterval', 'startN2', 'endN2', 'startCns', 'endCns', 'isDecoDive', 'summarizedDiveInfo', 'diveCount', 'avgVerticalSpeed', 'maxVerticalSpeed', 'floorsClimbed', 'floorsDescended', 'manufacturer', 'diveNumber', 'bottomTime', 'lapCount', 'flow', 'grit', 'jumpCount', 'caloriesEstimated', 'caloriesConsumed', 'waterEstimated', 'waterConsumed', 'maxAvgPower_1', 'maxAvgPower_2', 'maxAvgPower_5', 'maxAvgPower_10', 'maxAvgPower_20', 'maxAvgPower_30', 'maxAvgPower_60', 'maxAvgPower_120', 'maxAvgPower_300', 'maxAvgPower_600', 'maxAvgPower_1200', 'maxAvgPower_1800', 'maxAvgPower_3600', 'maxAvgPower_7200', 'maxAvgPower_18000', 'excludeFromPowerCurveReports', 'totalSets', 'activeSets', 'totalReps', 'minRespirationRate', 'maxRespirationRate', 'avgRespirationRate', 'trainingEffectLabel', 'activityTrainingLoad', 'avgFlow', 'avgGrit', 'minActivityLapDuration', 'avgStress', 'startStress', 'endStress', 'differenceStress', 'maxStress', 'aerobicTrainingEffectMessage', 'anaerobicTrainingEffectMessage', 'splitSummaries', 'isManualActivity', 'moderateIntensityMinutes', 'vigorousIntensityMinutes', 'maxBottomTime', 'hasSeedFirstbeatProfile', 'avgGradeAdjustedSpeed', 'avgWheelchairCadence', 'maxWheelchairCadence', 'avgJumpRopeCadence', 'maxJumpRopeCadence', 'differenceBodyBattery', 'gameType', 'beginPackWeight', 'fastestSplit_1000', 'fastestSplit_1609', 'fastestSplit_5000', 'fastestSplit_10000', 'fastestSplit_21098', 'fastestSplit_42195', 'fastestSplit_40000', 'fastestSplit_100', 'fastestSplit_400', 'fastestSplit_750', 'fastestSplit_1500', 'fastestSplit_91', 'fastestSplit_457', 'fastestSplit_914', 'fastestSplit_1508', 'impactLoad', 'avgStepSpeedLoss', 'avgStepSpeedLossPercent', 'hrTimeInZone_1', 'hrTimeInZone_2', 'hrTimeInZone_3', 'hrTimeInZone_4', 'hrTimeInZone_5', 'powerTimeInZone_1', 'powerTimeInZone_2', 'powerTimeInZone_3', 'powerTimeInZone_4', 'powerTimeInZone_5', 'powerTimeInZone_6', 'powerTimeInZone_7', 'longestPoolApneaInterval', 'avgForce', 'maxForce', 'normalizedForce', 'poolApneaBreathHoldDuration', 'deviceDisplayUnitsDTO', 'endTimeGMT', 'qualifyingDive', 'carbonOffset', 'packWeightCalories', 'standingTime', 'seatedTime', 'maxStandingPower', 'maxSeatedPower', 'avgStandingPower', 'avgSeatedPower', 'parent', 'decoDive', 'elevationCorrected', 'pr', 'manualActivity', 'favorite', 'autoCalcCalories')


def save(path, value):
    temporary = path.with_suffix('.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f, indent=2)
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def get_json(path, token):
    for attempt in range(3):
        try:
            return json.loads(api.request(path, 'Bearer ' + token))
        except urllib.error.HTTPError as error:
            if (error.code == 429 or error.code >= 500) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
        except (http.client.HTTPException, urllib.error.URLError, TimeoutError,
                ConnectionError, json.JSONDecodeError, UnicodeDecodeError):
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def normalize(series, payload):
    if series == 'hrv':
        rows = payload.get('hrvSummaries') if isinstance(payload, dict) else payload
        allowed = ('calendarDate', 'weeklyAvg', 'lastNightAvg', 'lastNight5MinHigh', 'status')
    elif series == 'sleep':
        rows = payload
        allowed = ('calendarDate', 'sleepTimeSeconds', 'napTimeSeconds', 'sleepWindowConfirmed', 'sleepWindowConfirmationType', 'sleepStartTimestampGMT', 'sleepEndTimestampGMT', 'sleepStartTimestampLocal', 'sleepEndTimestampLocal', 'autoSleepStartTimestampGMT', 'autoSleepEndTimestampGMT', 'sleepQualityTypePK', 'sleepResultTypePK', 'unmeasurableSleepSeconds', 'deepSleepSeconds', 'lightSleepSeconds', 'remSleepSeconds', 'awakeSleepSeconds', 'deviceRemCapable', 'sleepFromDevice', 'averageSpO2Value', 'lowestSpO2Value', 'highestSpO2Value', 'numberOfEventsBelowThreshold', 'averageSpO2HRSleep', 'spo2Threshold', 'averageRespirationValue', 'lowestRespirationValue', 'highestRespirationValue', 'awakeCount', 'avgSleepStress', 'ageGroup', 'avgHeartRate', 'sleepScoreFeedback', 'sleepScoreInsight', 'sleepScorePersonalizedInsight', 'sleepScores', 'sleepVersion', 'sleepNeed', 'nextSleepNeed', 'dailyNapDTOS', 'breathingDisruptionSeverity', 'sleepAlignment')
    else:
        rows = payload.get('data') if isinstance(payload, dict) else payload
        allowed = ('calendarDate',)
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise ValueError('Unexpected response structure')
    output = []
    for r in rows:
        item = {k: r[k] for k in allowed if k in r}
        if not item.get('calendarDate'):
            continue
        if series == 'wellness':
            for section in ('movement', 'calories', 'heartRate', 'intensityMinutes', 'stress',
                            'bodyBattery', 'hydration', 'respiration', 'pulseOx', 'jetLag'):
                obj = r.get(section)
                if isinstance(obj, dict):
                    item[section] = obj
        output.append(item)
    return output


def merge_range(previous, fresh, start, end, day_key='calendarDate'):
    """An empty successful response clears its range; failed ranges are never passed here."""
    return [r for r in previous if not start <= r.get(day_key, '')[:10] <= end] + fresh


def health_spans(previous, start, end, full=False):
    """Refresh recent readings and retry earlier failures without reloading every old week."""
    first = start if full or not previous else max(start, min(end, date.fromisoformat(previous.get('end', start.isoformat()))) - timedelta(days=6))
    spans = set()
    current = first
    while current <= end:
        until = min(current + timedelta(days=6), end)
        for series in ('sleep', 'hrv', 'wellness'):
            spans.add((series, current.isoformat(), until.isoformat()))
        current = until + timedelta(days=1)
    for row in previous.get('requests', []):
        if row.get('status') != 'ok' and row.get('series') in ('sleep', 'hrv', 'wellness'):
            a, b = max(start.isoformat(), row['start']), min(end.isoformat(), row['end'])
            if a <= b:
                spans.add((row['series'], a, b))
    return sorted(spans, key=lambda r: (r[1], r[0]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-06-01')
    parser.add_argument('--end', default=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat())
    parser.add_argument('--full', action='store_true', help='Refetch all health periods and extended data, including cached records.')
    parser.add_argument('--no-extended', action='store_true', help='Refresh only activity and recovery summaries.')
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start:
        raise SystemExit('End date must not precede start date.')
    settings = {}
    for line in (ROOT / '.env.local').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            settings[k.strip()] = v.strip().strip('"').strip("'")
    key = settings.get('GARMIN_PERSONAL_API_KEY', '')
    if not key or any(c in key for c in '\r\n'):
        raise SystemExit('Missing or invalid personal API key.')
    token = api.request('/personalapitoken-service/personal-api/personal-api-key/token', 'ApiKey ' + key, 'POST')
    try:
        decoded = json.loads(token)
        token = decoded if isinstance(decoded, str) else decoded.get('access_token') or decoded.get('accessToken') or decoded.get('token')
    except json.JSONDecodeError:
        pass
    if not isinstance(token, str) or not token or any(c.isspace() for c in token) or '<' in token:
        raise SystemExit('Unexpected token response; content withheld.')
    directory = ROOT / settings.get('GARMIN_DATA_DIR', './data/garmin')
    directory.mkdir(parents=True, exist_ok=True)
    history_path = directory / 'history.json'
    previous = json.loads(history_path.read_text()) if history_path.exists() else {}
    bundle = {**previous, 'start': min(previous.get('start', args.start), args.start),
              'end': max(previous.get('end', args.end), args.end), 'syncedAt': datetime.now().astimezone().isoformat(),
              'readinessStatus': 'Not exposed in the documented Garmin Personal API; no readiness score calculated.'}
    for series in ('activities', 'sleep', 'hrv', 'wellness', 'requests'):
        bundle.setdefault(series, [])
    activities = []
    # A full scan is committed only after pagination finishes, preserving prior history on failure.
    offset, seen = 0, set()
    while True:
        query = urlencode({'start': offset, 'limit': 99, 'startDate': args.start,
                           'endDate': args.end, 'sortOrder': 'desc', 'excludeChildren': 'true'})
        page = get_json('/activitylist-service/activities/search/activities?' + query, token)
        if not isinstance(page, list) or not all(isinstance(a, dict) for a in page):
            raise ValueError('Unexpected activity page structure')
        if not page:
            break
        new = 0
        for a in page:
            identity = a.get('activityId')
            if identity is None:
                raise ValueError('Activity ID missing')
            if identity in seen:
                continue
            seen.add(identity)
            new += 1
            item = {k: a[k] for k in FIELDS if k in a}
            kind = a.get('activityType')
            item['activityType'] = kind.get('typeKey') if isinstance(kind, dict) else kind
            activities.append(item)
        if not new:
            raise ValueError('Activity pagination repeated; prior history preserved')
        offset += len(page)
        print(f'Activities downloaded: {offset}', flush=True)
    bundle['activities'] = merge_range(bundle['activities'], activities, args.start, args.end, 'startTimeLocal')
    save(history_path, bundle)
    for series, a, b in health_spans(previous, start, end, args.full):
        paths = {
            'sleep': '/sleep-service/sleep/dailySleepSummariesByDate?' + urlencode({'startDate': a, 'endDate': b}),
            'hrv': f'/hrv-service/hrv/daily/{a}/{b}',
            'wellness': '/usersummary-service/v2/dailysummaries?' + urlencode({'startDate': a, 'endDate': b}),
        }
        status = {'series': series, 'start': a, 'end': b}
        try:
            rows = normalize(series, get_json(paths[series], token))
            rows = [r for r in rows if a <= r['calendarDate'] <= b]
            bundle[series] = merge_range(bundle[series], rows, a, b)
            status.update(status='ok', records=len(rows))
        except urllib.error.HTTPError as error:
            status.update(status='failed', reason=f'HTTP {error.code}', retained=True)
        except (urllib.error.URLError, TimeoutError, ValueError,
                http.client.HTTPException, ConnectionError):
            status.update(status='failed', reason='Network failure or unexpected response', retained=True)
        bundle['requests'] = [r for r in bundle['requests']
                              if not (r['series'] == series and a <= r['start'] and r['end'] <= b)]
        bundle['requests'].append(status)
        print(f'{series} {a} to {b}: {status["status"]}', flush=True)
        save(history_path, bundle)
    if not args.no_extended:
        from sync_available import run as sync_extended
        try:
            manifest = sync_extended(date.fromisoformat(bundle['start']), date.fromisoformat(bundle['end']), token, directory, args.full)
            print('Extended request failures:', sum(r['status'] != 'ok' for r in manifest['requests']), flush=True)
        finally:
            # Even if an extra endpoint fails, the completed summary sync is usable.
            build_dashboard.build()
    else:
        build_dashboard.build()
    failed = sum(r['status'] != 'ok' for r in bundle['requests'])
    print(f'Finished: {len(bundle["activities"])} activities, {len(bundle["sleep"])} sleep days, {len(bundle["hrv"])} HRV days. Failed health requests: {failed}.')


if __name__ == '__main__':
    try:
        # Scheduled and manual runs must not write the same history concurrently.
        with (ROOT / '.garmin-sync.lock').open('w') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SystemExit('A Garmin sync is already running.') from None
            main()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'Garmin returned HTTP {error.code}; body withheld.') from None
    except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
        raise SystemExit('Cannot reach Garmin. Run this script from your Terminal.') from None
