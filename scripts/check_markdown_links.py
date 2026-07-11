#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[1]
errors=[]
for file in [ROOT/'README.md', *sorted((ROOT/'docs').rglob('*.md'))]:
    text=file.read_text(encoding='utf-8')
    for number,line in enumerate(text.splitlines(),1):
        for match in re.finditer(r'!?\[[^]]*\]\(([^)]+)\)',line):
            link=match.group(1).strip().split()[0].strip('<>')
            if not link or re.match(r'^(https?://|mailto:|#)',link): continue
            target=(file.parent/unquote(link.split('#')[0])).resolve()
            if not target.exists(): errors.append(f'{file.relative_to(ROOT)}:{number}: {link}')
if errors:
    print('\n'.join(f'Link inexistente: {e}' for e in errors)); sys.exit(1)
print('Links Markdown OK.')
