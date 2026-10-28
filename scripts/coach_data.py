"""Read existing workbooks and assemble one personal coaching data source."""
from datetime import date, datetime, timedelta
from pathlib import Path
import posixpath
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import json

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def workbook_rows(path):
    """Read typed cells and cached formula results without modifying the workbook."""
    with ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(e.itertext()) for e in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            target = rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(archive.read(target)).findall('s:sheetData/s:row', NS):
                values = {'_row': int(row.attrib['r'])}
                for c in row:
                    value = c.find('s:v', NS)
                    raw = value.text if value is not None else None
                    kind = c.attrib.get('t')
                    if kind == 's' and raw is not None:
                        raw = strings[int(raw)]
                    elif kind == 'inlineStr':
                        inline = c.find('s:is', NS)
                        raw = ''.join(inline.itertext()) if inline is not None else None
                    elif kind not in ('str', 'e') and raw is not None:
                        try:
                            raw = float(raw)
                        except ValueError:
                            pass
                    values[''.join(x for x in c.attrib['r'] if x.isalpha())] = raw
                rows.append(values)
            result[sheet.attrib['name']] = rows
        return result


def number(value):
    return value if isinstance(value, (int, float)) else None


def excel_date(value):
    return (datetime(1899, 12, 30) + timedelta(days=value)).date().isoformat()


def imported_data(root=None):
    root = ROOT if root is None else Path(root)
    plan_path = root / 'Marathon_Plan.xlsx'
    food_path = root / 'outputs/calorie-tracker/Daily_Calorie_Tracker.xlsx'
    plan = workbook_rows(plan_path) if plan_path.exists() else {}
    profile_path = root / 'data/coach/profile.json'
    profile = {'name': 'Runner', 'proteinTarget': None, 'raceDate': None}
    if profile_path.exists():
        profile.update(json.loads(profile_path.read_text()))
    events = {}
    for row in plan.get('Training Plan', []):
        try:
            d = datetime.strptime(str(row.get('B')), '%d %b %Y').date().isoformat()
        except ValueError:
            continue
        events[d] = {'date': d, 'title': row.get('D'), 'description': row.get('E'), 'km': number(row.get('F')),
                     'pace': row.get('G'), 'hr': row.get('H'), 'fuel': row.get('I'), 'strength': row.get('J'),
                     'source': 'Marathon_Plan.xlsx / Training Plan', 'week': number(row.get('A'))}
    # Calendar supplies explicit rest days absent from the session table.
    monday = date.fromisoformat(profile.get('calendarStart', '2026-09-14'))
    for i, row in enumerate(plan.get('Calendar', [])[2:14]):
        for offset, column in enumerate('BCDEFGH'):
            d = (monday + timedelta(weeks=i, days=offset)).isoformat()
            if d not in events:
                text = row.get(column)
                if isinstance(text, str):
                    events[d] = {'date': d, 'title': 'Rest' if 'rest' in text.lower() else text.split('\n')[-1],
                                 'description': text, 'source': 'Marathon_Plan.xlsx / Calendar'}
    override_path = root / 'data/coach/calendar_overrides.json'
    overrides = json.loads(override_path.read_text()) if override_path.exists() else []
    for override in overrides:
        d = date.fromisoformat(override['date']).isoformat()
        original = events.get(d, {'date': d})
        events[d] = {**original, **override, 'originalKm': original.get('km'),
                     'overrideSource': override.get('overrideSource', 'Your calendar override')}
    strength = []
    for section, start, finish in [('A', 11, 16), ('B', 20, 25)]:
        for row_index in range(start, finish + 1):
            row = next((r for r in plan.get('Strength (No Gym)', []) if r['_row'] == row_index), None)
            if not row:
                continue
            strength.append({'section': section, 'exercise': row.get('A'), 'early': row.get('B'),
                             'middle': row.get('C'), 'late': row.get('D'), 'instructions': row.get('E')})
    nutrition = workbook_rows(food_path) if food_path.exists() else {}
    meals = []
    for i, row in enumerate(nutrition.get('Food log', [])):
        if not number(row.get('A')) or not row.get('C') or row.get('B') == 'Example' or row.get('N') == 'Planned':
            continue
        qty = number(row.get('D'))
        def amount(column):
            rate = number(row.get(column))
            return qty * rate if qty is not None and rate is not None else None
        meals.append({'id': f'import-food-{i}', 'date': excel_date(row['A']), 'meal': row.get('B'), 'food': row.get('C'),
                      'quantity': qty, 'unit': row.get('E'), 'kcal': amount('F'), 'protein': amount('J'),
                      'carbs': amount('K'), 'notes': row.get('I'), 'source': 'Imported food workbook'})
    weights = []
    for row in nutrition.get('Daily totals', []):
        if not number(row.get('A')):
            continue
        for col, timing in [('E', 'morning'), ('L', 'evening')]:
            if number(row.get(col)):
                weights.append({'date': excel_date(row['A']), 'timing': timing, 'kg': row[col]})
    return {'calendar': sorted(events.values(), key=lambda x: x['date']), 'strength': strength, 'meals': meals,
            'weights': weights, 'profile': profile,
            'sources': ([str(p.relative_to(root)) for p in (plan_path, food_path, profile_path, override_path) if p.exists()]
                        + ['Garmin Personal API (activities and recovery)'])}


def journal():
    from training_store import load_journal
    return load_journal()


def state():
    from training_store import coach_state
    return coach_state()
