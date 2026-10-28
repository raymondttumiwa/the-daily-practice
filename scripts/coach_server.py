"""Serve the personal training desk on localhost, with persistent meal/workout logs."""
import argparse
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import threading
from urllib.parse import urlparse
from uuid import uuid4

import build_dashboard
import coach_data

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.RLock()


def validate(payload, kind):
    if not isinstance(payload, dict):
        raise ValueError('Expected a JSON object.')
    date.fromisoformat(payload.get('date', ''))
    item = {'date': payload['date'], 'id': uuid4().hex, 'createdAt': datetime.now().isoformat()}
    specs = {
        'meals': (('food', 'meal', 'notes', 'status', 'unit'), ('quantity', 'kcal', 'protein', 'carbs')),
        'workouts': (('exercise', 'notes'), ('sets', 'reps', 'minutes', 'effort')),
        'checkins': (('notes', 'timing'), ('kg', 'fatigue', 'soreness')),
    }
    texts, numbers = specs[kind]
    for k in texts:
        value = payload.get(k, '')
        if not isinstance(value, str) or len(value) > 2000:
            raise ValueError('Invalid text input.')
        item[k] = value.strip()
    for k in numbers:
        value = payload.get(k)
        if value is None or value == '':
            item[k] = None
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100000:
            raise ValueError('Numeric values must be nonnegative and finite.')
        else:
            item[k] = value
    if kind == 'meals':
        if not item['food'] or any(item[k] is None for k in ('kcal', 'protein', 'carbs')):
            raise ValueError('Food, calories, protein and carbs are required; zero is valid.')
        if item['status'] not in ('planned', 'eaten'):
            raise ValueError('Choose planned or eaten.')
    if kind == 'workouts' and not item['exercise']:
        raise ValueError('Enter an exercise or workout name.')
    if kind == 'checkins':
        if item['timing'] not in ('morning', 'evening'):
            raise ValueError('Choose morning or evening.')
        if not isinstance(payload.get('pain', False), bool):
            raise ValueError('Invalid pain flag.')
        item['pain'] = payload.get('pain', False)
        if any(item[k] is not None and not 0 <= item[k] <= 5 for k in ('fatigue', 'soreness')):
            raise ValueError('Fatigue and soreness must be between 0 and 5.')
        if item['kg'] is not None and not 20 <= item['kg'] <= 350:
            raise ValueError('Check weight in kilograms.')
    return item


def persist(journal):
    from training_store import save_journal
    save_journal(journal)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not log health input or request bodies.

    def respond(self, value, status=200, content_type='application/json'):
        body = json.dumps(value).encode() if content_type == 'application/json' else value
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def permitted_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def do_GET(self):
        if not self.permitted_host():
            return self.respond({'error': 'Invalid host.'}, 403)
        path = urlparse(self.path).path
        if path == '/api/state':
            return self.respond(coach_data.state())
        if path == '/':
            return self.respond((ROOT / 'outputs/garmin-dashboard/index.html').read_bytes(), content_type='text/html')
        self.respond({'error': 'Not found.'}, 404)

    def do_POST(self):
        expected_origins = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if not self.permitted_host() or self.headers.get('Origin') not in expected_origins:
            return self.respond({'error': 'Use the local dashboard to save changes.'}, 403)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16000:
                raise ValueError('Invalid request size.')
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError('Expected a JSON object.')
            route = urlparse(self.path).path
            with LOCK:
                journal = coach_data.journal()
                kind = route.removeprefix('/api/')
                if kind in ('meals', 'workouts', 'checkins'):
                    journal[kind].append(validate(payload, kind))
                elif kind == 'settings':
                    hours = payload.get('sleepTargetHours')
                    if isinstance(hours, bool) or not isinstance(hours, (int, float)) or not math.isfinite(hours) or not 7 <= hours <= 10:
                        raise ValueError('Sleep target must be between 7 and 10 hours.')
                    journal.setdefault('settings', {})['sleepTargetHours'] = hours
                elif kind == 'meal-status':
                    if payload.get('status') not in ('eaten', 'planned'):
                        raise ValueError('Invalid meal status.')
                    match = next((m for m in journal['meals'] if m['id'] == payload.get('id')), None)
                    if not match:
                        raise ValueError('Meal not found.')
                    match['status'] = payload['status']
                elif kind == 'delete':
                    collection = payload.get('collection')
                    if collection not in ('meals', 'workouts', 'checkins'):
                        raise ValueError('Invalid collection.')
                    journal[collection] = [r for r in journal[collection] if r['id'] != payload.get('id')]
                else:
                    return self.respond({'error': 'Not found.'}, 404)
                persist(journal)
            self.respond(coach_data.state())
        except (ValueError, TypeError, KeyError):
            self.respond({'error': 'Check your entries, units, required fields and date.'}, 400)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    build_dashboard.build()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Personal training desk: http://127.0.0.1:{args.port}', flush=True)
    print('Keep this process running while logging. Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
