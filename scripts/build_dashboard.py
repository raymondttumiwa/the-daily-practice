"""Build the private training desk or a public preview with fictional data."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_FIELDS = ('startTimeLocal','activityType','distance','duration','movingDuration','elapsedDuration',
                   'averageHR','maxHR','averageSpeed','calories','aerobicTrainingEffect','anaerobicTrainingEffect',
                   'elevationGain','elevationLoss','activityTrainingLoad','vO2MaxValue','avgPower','maxPower',
                   'averageRunningCadenceInStepsPerMinute','avgStrideLength','hrTimeInZone_1','hrTimeInZone_2',
                   'hrTimeInZone_3','hrTimeInZone_4','hrTimeInZone_5')


def build(demo=False, output=None):
    if demo:
        from demo_data import bundle
        data = bundle()
    else:
        from training_store import history_bundle, backup
        from coach_data import state
        data = history_bundle()
        data['coach'] = state()
        backup()
    # Explicitly select publishable activity fields; raw extras never enter HTML.
    data['activities'] = [{k:row[k] for k in ACTIVITY_FIELDS if k in row} for row in data['activities']]
    data['builtAt'] = __import__('datetime').datetime.now().astimezone().isoformat()
    from history_dashboard import render
    from coach_ui import enhance
    html = enhance(render(data))
    target = Path(output) if output else ROOT / ('site/index.html' if demo else 'outputs/garmin-dashboard/index.html')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(html)
    temporary.replace(target)
    print(f'Built {"demo" if demo else "personal"} dashboard: {len(data["activities"])} activities → {target}')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Use fictional data; safe for GitHub Pages.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.demo, args.output)
