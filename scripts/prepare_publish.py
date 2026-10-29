"""Prepare code and a fictional demo without copying any personal source records."""
import argparse
from pathlib import Path
import shutil

import build_dashboard

ROOT = Path(__file__).resolve().parents[1]
FILES = ['.gitignore', '.env.example', 'README.md', 'README-Garmin.md', 'FILES.md',
         '.github/workflows/pages.yml', 'references/Background.jpg',
         'docs/GARMIN-DATA.md', 'docs/garmin-api-catalog.json', 'docs/ROADMAP.md']
FILES += ['scripts/' + name for name in (
    'build_dashboard.py', 'check_garmin.py', 'coach_data.py', 'coach_server.py', 'coach_ui.py',
    'demo_data.py', 'history_dashboard.py', 'install_daily_sync.py', 'prepare_publish.py',
    'sync_available.py', 'sync_garmin.py', 'sync_history.py', 'training_store.py')]
FILES += ['assets/' + name for name in ('coach.js', 'dashboard.css', 'desk.html', 'history.html', 'history.js', 'Favicon.png', 'brand-logo.png')]
FILES += ['tests/' + name for name in ('test_store.py', 'test_sync.py', 'dashboard.mjs')]


def prepare(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    for name in FILES:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    build_dashboard.build(demo=True, output=destination / 'site/index.html')
    (destination / 'site/.nojekyll').touch()
    print('Clean publishing bundle:', destination)
    print('Includes code and fictional demo only. Private source records were not copied.')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path, help='A new, empty folder outside your personal data.')
    prepare(parser.parse_args().destination)
