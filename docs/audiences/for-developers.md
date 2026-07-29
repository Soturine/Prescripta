# Guia para desenvolvedores

O Prescripta usa FastAPI, Pydantic, SQLAlchemy, React, TypeScript e Vite.

## Pontos de entrada

- Backend: `backend/app`.
- Entidades: `backend/app/domain` e `backend/app/database/models.py`.
- Regras: `backend/app/services`.
- Integrações: `backend/app/integrations`.
- Relatórios: `backend/app/reports`.
- Frontend: `frontend/src`.
- Docs: `docs`.

## Convenções importantes

- Regra clínica fica em services, não em rotas FastAPI nem componentes React.
- IA não decide risco, dose, status ou protocolo.
- Dados extraídos por IA entram como `pending_review`.
- O backend é a fonte real de autorização.
- API Key nunca vai para frontend, logs, relatórios ou auditoria.

## Comandos

```powershell
cd backend
..\.venv\Scripts\python -m ruff check . --no-cache
..\.venv\Scripts\python -m pytest --basetemp=..\.tmp\pytest
```

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
```

Consulte também o [guia de TI e integrações](for-it-and-integrations.md) e o `AGENTS.md` na raiz.
