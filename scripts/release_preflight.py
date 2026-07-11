#!/usr/bin/env python3
"""Gate local: valida, envia a main e aguarda o CI antes de permitir uma tag."""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(*args: str, cwd: Path=ROOT, capture: bool=False) -> str:
    result=subprocess.run(args,cwd=cwd,text=True,capture_output=capture,check=False)
    if result.returncode: raise SystemExit(result.stderr or result.stdout or f"Falhou: {' '.join(args)}")
    return result.stdout.strip() if capture else ""
if run('git','status','--porcelain',capture=True): raise SystemExit('Worktree deve estar limpa.')
if run('git','branch','--show-current',capture=True) != 'main': raise SystemExit('Execute somente na branch main.')
if 'APP_VERSION = "8.6.0"' not in (ROOT/'backend/app/core/version.py').read_text(encoding='utf-8'): raise SystemExit('Versão esperada 8.6.0 não encontrada.')
run(sys.executable,'scripts/check_text_quality.py'); run(sys.executable,'scripts/check_markdown_links.py'); run(sys.executable,'scripts/check_assets.py')
run(sys.executable,'-m','ruff','check','.', '--no-cache',cwd=ROOT/'backend'); run(sys.executable,'-m','pytest','--maxfail=1',cwd=ROOT/'backend')
run('npm','run','lint',cwd=ROOT/'frontend'); run('npm','run','test','--','--run',cwd=ROOT/'frontend'); run('npm','run','build',cwd=ROOT/'frontend')
sha=run('git','rev-parse','HEAD',capture=True); run('git','push','origin','main')
for _ in range(60):
    raw=run('gh','run','list','--workflow','ci.yml','--commit',sha,'--json','databaseId,status,conclusion,url','--limit','1',capture=True)
    runs=json.loads(raw or '[]')
    if runs:
        item=runs[0]
        if item['status']=='completed':
            if item['conclusion']!='success': raise SystemExit(f"CI falhou: {item['url']}")
            print(f"CI verde: {item['url']}\nPreflight aprovado; a tag pode ser criada."); sys.exit(0)
    time.sleep(10)
raise SystemExit('Timeout aguardando GitHub Actions; não crie a tag.')
