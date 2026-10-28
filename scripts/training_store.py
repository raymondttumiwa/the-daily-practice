"""Transactional local training database. JSON downloads and workbook sources stay intact."""
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


@contextmanager
def connection():
    folder = ROOT / 'data'
    folder.mkdir(exist_ok=True)
    path = folder / 'training.sqlite3'
    db = sqlite3.connect(path, timeout=30)
    path.chmod(0o600)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS records (
        collection TEXT NOT NULL, source TEXT NOT NULL, key TEXT NOT NULL,
        day TEXT, payload TEXT NOT NULL, PRIMARY KEY(collection,source,key));
      CREATE INDEX IF NOT EXISTS records_by_day ON records(collection,day);
      CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS imports (path TEXT PRIMARY KEY, signature TEXT NOT NULL);
    ''')
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def _meta(db, key, value):
    db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (key, encode(value)))


def _records(db, collection, source, rows):
    db.execute('DELETE FROM records WHERE collection=? AND source=?', (collection, source))
    for index, row in enumerate(rows):
        key = str(row.get('id', row.get('activityId', row.get('calendarDate', index))))
        day = row.get('date') or row.get('calendarDate') or row.get('startTimeLocal', '')[:10]
        db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?,?)',
                   (collection, source, key, day, encode(row)))


def _rows(db, collection, source=None):
    sql = 'SELECT payload FROM records WHERE collection=?'
    args = [collection]
    if source:
        sql += ' AND source=?'
        args.append(source)
    return [json.loads(row[0]) for row in db.execute(sql+' ORDER BY day,key', args)]


def load_journal():
    with connection() as db:
        initialized = db.execute("SELECT value FROM metadata WHERE key='journal_initialized'").fetchone()
        if not initialized:
            path = ROOT / 'data/coach/journal.json'
            value = json.loads(path.read_text()) if path.exists() else {}
            for key in ('meals', 'workouts', 'checkins'):
                _records(db, key, 'journal', value.get(key, []))
            _meta(db, 'journal_settings', value.get('settings', {}))
            _meta(db, 'journal_initialized', True)
        settings = db.execute("SELECT value FROM metadata WHERE key='journal_settings'").fetchone()
        return {**{key: _rows(db, key, 'journal') for key in ('meals', 'workouts', 'checkins')},
                'settings': json.loads(settings[0]) if settings else {}}


def save_journal(value):
    with connection() as db:
        for key in ('meals', 'workouts', 'checkins'):
            _records(db, key, 'journal', value.get(key, []))
        _meta(db, 'journal_settings', value.get('settings', {}))
        _meta(db, 'journal_initialized', True)
        _meta(db, 'journal_saved_at', datetime.now().isoformat())
    # Compatibility export; SQLite is the source of truth for new entries.
    folder = ROOT / 'data/coach'
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder / 'journal.tmp'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
    temporary.replace(folder / 'journal.json')


def garmin_directory():
    settings = {}
    env = ROOT / '.env.local'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip().strip('"').strip("'")
    return ROOT / settings.get('GARMIN_DATA_DIR', 'data/garmin')


def refresh():
    """Import changed sources atomically, with stable IDs so repeated builds are safe."""
    import coach_data
    load_journal()
    directory = garmin_directory()
    with connection() as db:
        def changed(path):
            signature = hashlib.sha256(path.read_bytes()).hexdigest()
            previous = db.execute('SELECT signature FROM imports WHERE path=?', (str(path),)).fetchone()
            return signature if not previous or previous[0] != signature else None
        def mark(path, signature):
            db.execute('INSERT OR REPLACE INTO imports VALUES (?,?)', (str(path), signature))
        source_paths = [p for p in (ROOT / 'Marathon_Plan.xlsx', ROOT / 'outputs/calorie-tracker/Daily_Calorie_Tracker.xlsx',
                                    ROOT / 'data/coach/profile.json', ROOT / 'data/coach/calendar_overrides.json') if p.exists()]
        signatures = [changed(path) for path in source_paths]
        if any(signatures) or not db.execute("SELECT 1 FROM metadata WHERE key='profile'").fetchone():
            value = coach_data.imported_data(ROOT)
            for key in ('meals', 'weights', 'calendar', 'strength'):
                _records(db, key, 'workbook', value[key])
            _meta(db, 'profile', value['profile'])
            _meta(db, 'sources', value['sources'])
            for path in source_paths:
                mark(path, hashlib.sha256(path.read_bytes()).hexdigest())
        history = directory / 'history.json'
        if history.exists() and (signature := changed(history)):
            value = json.loads(history.read_text())
            for key in ('activities', 'sleep', 'hrv', 'wellness'):
                _records(db, key, 'garmin', value.get(key, []))
            _meta(db, 'history', {k: v for k, v in value.items() if k not in ('activities','sleep','hrv','wellness','coach')})
            mark(history, signature)
        for path in sorted((directory / 'extended').glob('*.json')):
            if not (signature := changed(path)):
                continue
            try:
                value = json.loads(path.read_text())
            except (ValueError, UnicodeDecodeError):
                continue
            db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?,?)',
                       ('extended', 'garmin', path.stem, None, encode(value)))
            mark(path, signature)
        _meta(db, 'database_updated_at', datetime.now().isoformat())


def coach_state():
    refresh()
    with connection() as db:
        result = {key: _rows(db, key, 'workbook') for key in ('calendar','strength','meals','weights')}
        for key in ('profile','sources'):
            row = db.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
            result[key] = json.loads(row[0]) if row else ({} if key == 'profile' else [])
    result['journal'] = load_journal()
    return result


def history_bundle():
    refresh()
    with connection() as db:
        row = db.execute("SELECT value FROM metadata WHERE key='history'").fetchone()
        result = json.loads(row[0]) if row else {'start':'2026-06-01','end':datetime.now().date().isoformat()}
        result.update({key: _rows(db, key, 'garmin') for key in ('activities','sleep','hrv','wellness')})
        extra = {row['key']: json.loads(row['payload']) for row in db.execute("SELECT key,payload FROM records WHERE collection='extended'")}
    # Merge selected documented fields only. Keep raw detail and identities out of HTML.
    for row in result['activities']:
        detail = extra.get('activity-'+str(row.get('activityId')), {})
        summary = detail.get('summaryDTO', {}) if isinstance(detail, dict) else {}
        aliases = {'activityTrainingLoad':'activityTrainingLoad','averageRunCadence':'averageRunningCadenceInStepsPerMinute',
                   'averagePower':'avgPower','trainingEffect':'aerobicTrainingEffect', 'strideLength':'avgStrideLength'}
        for source, target in aliases.items():
            if row.get(target) is None and isinstance(summary, dict) and summary.get(source) is not None:
                row[target] = summary[source]
    fitness = []
    for key, value in extra.items():
        if key.startswith('fitness-age-') and isinstance(value, dict) and isinstance(value.get('fitnessAge'), (int,float)):
            fitness.append({'calendarDate':key[-10:],'fitnessAge':value['fitnessAge']})
    result['fitnessAge'] = sorted(fitness, key=lambda x:x['calendarDate'])
    result['database'] = {'extendedRecords':len(extra), 'activities':len(result['activities'])}
    manifest = extra.get('manifest', {})
    result['extendedSync'] = {'updated':manifest.get('updated'),
                              'failures':[{'series':r.get('series'), 'reason':r.get('reason')}
                                          for r in manifest.get('requests', []) if r.get('status') != 'ok']}
    result['availability'] = availability(result, extra)
    return result


def availability(bundle, extra):
    """Summarize non-null usable values, rather than claiming all schema fields exist."""
    fields = [('Training load','activities','activityTrainingLoad','points'),('Running cadence','activities','averageRunningCadenceInStepsPerMinute','spm'),
              ('Power','activities','avgPower','W'),('VO₂ max','activities','vO2MaxValue','ml/kg/min'),
              ('Sleep','sleep','sleepTimeSeconds','seconds'),('HRV','hrv','lastNightAvg','ms'),
              ('Resting HR','wellness','heartRate.restingValue','bpm'),('Steps','wellness','movement.steps.value','steps'),
              ('Respiration','wellness','respiration.avgValue','breaths/min'),('SpO₂','wellness','pulseOx.avgValue','%'),
              ('Energy burned','wellness','calories.burnedTotal','kcal'),('Fitness age','fitnessAge','fitnessAge','years')]
    output=[]
    for label,collection,key,unit in fields:
        values=[]
        for row in bundle.get(collection,[]):
            v=row
            for part in key.split('.'):
                v=v.get(part) if isinstance(v,dict) else None
            if isinstance(v,(int,float)) and not isinstance(v,bool) and v>0:
                values.append(v)
        output.append({'label':label,'records':len(values),'unit':unit})
    return output


def backup():
    folder = ROOT / 'data/backups'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ('training-'+datetime.now().strftime('%Y-%m-%d')+'.sqlite3')
    with connection() as source:
        target = sqlite3.connect(path)
        try:
            source.backup(target)
        finally:
            target.close()
    path.chmod(0o600)
    return path


if __name__ == '__main__':
    refresh()
    result = history_bundle()
    print('Database updated:', ROOT / 'data/training.sqlite3')
    print('Activities:',len(result['activities']),'· extended records:',result['database']['extendedRecords'])
    print('Backup:',backup())
