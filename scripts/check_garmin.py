"""Test the official Garmin Personal API without printing or saving credentials."""
import json
import re
from pathlib import Path
import urllib.error
import urllib.request

root = Path(__file__).resolve().parents[1]
settings = {}
for line in (root / '.env.local').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        name, value = line.split('=', 1)
        settings[name.strip()] = value.strip().strip('"').strip("'")

key = settings.get('GARMIN_PERSONAL_API_KEY', '')
if not key or '\n' in key or '\r' in key:
    raise SystemExit('Missing or invalid GARMIN_PERSONAL_API_KEY in .env.local.')

# Endpoint documented at https://developer.garmin.com/gc-developer-program/personal/personal-api/
request = urllib.request.Request(
    'https://personal.connectapi.garmin.com/personalapitoken-service/personal-api/personal-api-key/token',
    data=b'',
    headers={'Authorization': 'ApiKey ' + key},
    method='POST',
)
try:
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read()
        text = body.decode('utf-8', errors='replace').strip()
        print('HTTP status:', response.status)
        print('Response type:', response.headers.get_content_type())
        print('Redirected:', response.geturl() != request.full_url)
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = None
        # Never output response text: it could itself be a credential.
        candidate = result if isinstance(result, str) else text
        if not text:
            print('Empty response. Authentication is not yet verified.')
        elif isinstance(result, dict):
            token = next((result.get(name) for name in
                          ('access_token', 'accessToken', 'token')
                          if isinstance(result.get(name), str) and result.get(name)), None)
            if token:
                print('Token field received. Token value withheld.')
            else:
                print('JSON object received without a recognized token field. Authentication is not yet verified.')
        elif re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', candidate):
            print('JWT-shaped token received as text. Value withheld; API access still needs verification.')
        elif candidate.lstrip().lower().startswith(('<!doctype html', '<html')):
            print('HTML page received instead of a token. Authentication is not yet verified.')
        else:
            print('Unrecognized response format. Body withheld; authentication is not yet verified.')
        print('No credentials or token values were printed or saved.')
except urllib.error.HTTPError as error:
    raise SystemExit(f'Garmin returned HTTP {error.code}. Check key validity and expiration.') from None
except urllib.error.URLError:
    raise SystemExit('Cannot reach Garmin. Check DNS/network access and endpoint availability.') from None
except (TimeoutError, OSError):
    raise SystemExit('Network connection failed or timed out. Try again when connectivity is available.') from None
