#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.github', '.venv', '.pytest_cache', '.ruff_cache', '__pycache__'}
PATTERNS = [
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'X-Amz-Signature='),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'Authorization:\s*Bearer\s+[A-Za-z0-9._~+/-]+=*', re.I),
    re.compile(r'(WHOOP_CLIENT_SECRET|client_secret|access_token|refresh_token)\s*[:=]\s*["\']?[A-Za-z0-9._~+/-]{12,}', re.I),
]
ALLOW = {'scripts/privacy-check.py'}
failed = False
for path in ROOT.rglob('*'):
    if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
        continue
    rel = path.relative_to(ROOT).as_posix()
    if rel in ALLOW:
        continue
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if any(p.search(line) for p in PATTERNS):
            print(f'{rel}:{i}: secret-like pattern')
            failed = True
if failed:
    raise SystemExit(1)
print('privacy_check_ok')
