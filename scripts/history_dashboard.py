"""Standalone history renderer. UI assets remain editable; no frontend dependencies."""
import json
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def render(bundle):
    payload = json.dumps(bundle, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return (ASSETS / 'history.html').read_text().replace('__HISTORY_SCRIPT__', (ASSETS / 'history.js').read_text()).replace('__DATA__', payload)
