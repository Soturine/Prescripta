#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
required_v860 = {
    'login-v8.6.0.png', 'dashboard-clinical-v8.6.0.png', 'dashboard-admin-v8.6.0.png',
    'dashboard-auditor-v8.6.0.png', 'patients-list-v8.6.0.png', 'patient-details-v8.6.0.png',
    'patient-history-v8.6.0.png', 'patient-documents-v8.6.0.png', 'medications-catalog-v8.6.0.png',
    'medication-details-v8.6.0.png', 'medication-curation-v8.6.0.png', 'prescription-clinical-v8.6.0.png',
    'prescription-technical-v8.6.0.png', 'dose-intelligence-v8.6.0.png', 'psychotropic-safety-v8.6.0.png',
    'prescribing-policy-v8.6.0.png', 'protocols-list-v8.6.0.png', 'protocol-run-v8.6.0.png',
    'imports-v8.6.0.png', 'reports-v8.6.0.png', 'audit-v8.6.0.png', 'ai-settings-v8.6.0.png',
    'users-specialties-v8.6.0.png', 'mobile-v8.6.0.png', 'tablet-v8.6.0.png',
    'prescripta-v8.6.0-main-demo.gif', 'prescripta-v8.6.0-clinical-flow.gif',
    'prescripta-v8.6.0-admin-flow.gif', 'prescripta-v8.6.0-audit-flow.gif', 'prescripta-v8.6.0-mobile-flow.gif',
}
for version in (ROOT/'docs/assets').glob('v*'):
    groups=defaultdict(list)
    for file in version.iterdir():
        if file.suffix.lower() in {'.png','.gif','.jpg','.jpeg'}:
            if file.stat().st_size==0: errors.append(f'Asset vazio: {file.relative_to(ROOT)}')
            groups[hashlib.sha256(file.read_bytes()).hexdigest()].append(file.name)
    if version.name == 'v8.6.0':
        missing = required_v860 - {file.name for file in version.iterdir() if file.is_file()}
        errors.extend(f'Asset obrigatório ausente: {name}' for name in sorted(missing))
        for names in groups.values():
            if len(names)>1: errors.append(f'Hashes duplicados em {version.name}: {", ".join(names)}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print('Assets OK.')
