"""Install a macOS LaunchAgent for daily Garmin sync at 22:00 local time."""
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'com.raymond.garmin-sync'
python = shutil.which('python3') or sys.executable
logs = ROOT / 'logs'
logs.mkdir(exist_ok=True)
config = {
    'Label': LABEL,
    'ProgramArguments': [python, '-u', str(ROOT / 'scripts/sync_history.py')],
    'WorkingDirectory': str(ROOT),
    'StartCalendarInterval': {'Hour': 22, 'Minute': 0},
    'RunAtLoad': True,
    'StandardOutPath': str(logs / 'garmin-sync.log'),
    'StandardErrorPath': str(logs / 'garmin-sync-error.log'),
    'ProcessType': 'Background',
    'Umask': 63,
    'EnvironmentVariables': {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin', 'PYTHONUNBUFFERED': '1'},
}
prepared = ROOT / 'scripts' / f'{LABEL}.plist'
prepared.write_bytes(plistlib.dumps(config))
target = Path.home() / 'Library/LaunchAgents' / f'{LABEL}.plist'
try:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(prepared, target)
    target.chmod(0o600)
except PermissionError:
    raise SystemExit('Cannot write ~/Library/LaunchAgents from this environment. Run python3 scripts/install_daily_sync.py in your Terminal.') from None
domain = f'gui/{os.getuid()}'
subprocess.run(['launchctl', 'bootout', f'{domain}/{LABEL}'], capture_output=True)
result = subprocess.run(['launchctl', 'bootstrap', domain, str(target)], capture_output=True, text=True)
if result.returncode:
    raise SystemExit(f'LaunchAgent saved but activation failed (exit {result.returncode}). Check launchctl in your Terminal.')
check = subprocess.run(['launchctl', 'print', f'{domain}/{LABEL}'], capture_output=True, text=True)
if check.returncode:
    raise SystemExit('Activation could not be verified.')
print('Daily Garmin sync installed and verified: 22:00 local Mac time, plus an immediate sync on loading.')
print('Log:', logs / 'garmin-sync.log')
