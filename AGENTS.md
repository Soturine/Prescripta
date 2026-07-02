# AGENTS.md

Guia para agentes e colaboradores que forem evoluir o Prescripta.

## Layout

- `backend/app/domain`: entidades, enums e objetos de resultado.
- `backend/app/services`: regras determinísticas e serviços de aplicação.
- `backend/app/core/auth.py`: dependências de autenticação e autorização.
- `backend/app/core/security.py`: hash de senha e JWT.
- `backend/app/repositories`: acesso a dados via SQLAlchemy.
- `backend/app/api/routes`: endpoints FastAPI.
- `backend/tests`: testes unitários e de API.
- `frontend/src/pages`: telas de navegação.
- `frontend/src/components`: componentes reutilizáveis.
- `frontend/src/services`: cliente HTTP e integração com API.
- `docs`: documentação de arquitetura, produto, regras clínicas, segurança e releases.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd frontend
npm install
```

## Testes

```powershell
cd backend
..\.venv\Scripts\python -m pytest
```

```powershell
cd frontend
npm run build
```

## Lint

```powershell
cd backend
..\.venv\Scripts\python -m ruff check . --no-cache
```

```powershell
cd frontend
npm run lint
```

## Convenções

- Use TypeScript estrito no frontend.
- Use Pydantic para contratos de API e SQLAlchemy para persistência.
- Não misture regra de negócio com componentes React.
- Não implemente regra de risco diretamente em rota FastAPI; use `backend/app/services`.
- Backend é a fonte real de autorização; frontend pode esconder menus, mas nunca substituir checagem de perfil.
- Não registre senha em auditoria, log ou payload de resposta.
- Ao alterar permissões, atualize testes e `docs/security/authentication-and-roles.md`.
- Mantenha IA fora do MVP. Quando entrar no roadmap, IA deve apenas explicar alertas gerados por regras determinísticas.
- Atualize documentação quando alterar comportamento de produto, API, regra clínica ou segurança.
- Atualize `CHANGELOG.md` em mudanças relevantes.
- Não versionar `.env`, bancos locais, caches, `node_modules` ou `dist`.
- Não usar dados sensíveis reais em seeds, testes ou exemplos.

## Commits

Use Conventional Commits:

- `feat(backend): ...`
- `feat(frontend): ...`
- `test(backend): ...`
- `docs: ...`
- `ci: ...`
- `chore(release): ...`
