# Prescripta Para Desenvolvedores E TI

Prescripta usa FastAPI, Pydantic, SQLAlchemy, React, TypeScript e Vite.

## Pontos De Entrada

- Backend: `backend/app`.
- Entidades: `backend/app/domain` e `backend/app/database/models.py`.
- Regras: `backend/app/services`.
- Integracoes: `backend/app/integrations`.
- Relatórios: `backend/app/reports`.
- Frontend: `frontend/src`.
- Docs: `docs`.

## Convencoes Importantes

- Regra clínica fica em services, não em rotas FastAPI nem componentes React.
- IA não decide risco, dose, status ou protocolo.
- Dados extraidos por IA entram como `pending_review`.
- Backend e a fonte real de autorizacao.
- API Key nunca vai para frontend, logs, relatórios ou auditoria.

## Comandos

```powershell
cd backend
..\.venv\Scripts\python -m ruff check . --no-cache
..\.venv\Scripts\python -m pytest
```

```powershell
cd frontend
npm run lint
npm run build
```
