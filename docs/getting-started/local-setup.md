# Setup Local

Para um roteiro ainda mais curto, veja `docs/setup/quickstart.md`. Para
problemas comuns, veja `docs/setup/troubleshooting.md`.

## Caminho Recomendado

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-install.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

O setup cria `.venv`, instala `backend/requirements.txt` e executa `npm install` no frontend. O
`dev.ps1` sobe backend e frontend em janelas separadas. Dependências de teste do backend ficam em
`backend/requirements-dev.txt` e não são instaladas pelo setup básico.

Política suportada no `main`: Python 3.12+, Node.js 22+ e npm 11.18.0. A matriz de CI usa Python 3.12
e Node.js 24. Para Linux/macOS, Docker é o caminho cross-platform documentado; não há script shell
equivalente ao fluxo PowerShell nesta rodada.

## Reset Do Banco Demo

```powershell
powershell -ExecutionPolicy Bypass -File scripts/reset-demo-db.ps1
```

O reset remove apenas o banco SQLite demo dentro do workspace e recria os dados de
exemplo. Não use dados reais de paciente.

## Variáveis Úteis

- `PRESCRIPTA_ENV=development`
- `PRESCRIPTA_DATABASE_URL=sqlite:///./prescripta.db`
- `PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS=false`
- `PRESCRIPTA_CONFIG_ENCRYPTION_KEY=troque-esta-chave-local`

## Health

`GET /api/health` retorna nome, versão, ambiente, banco, provider de IA e se
chamadas externas estão habilitadas. A resposta não inclui segredo.

## URLs locais

- frontend: <http://127.0.0.1:5173>
- API/health: <http://127.0.0.1:8000/api/health>
- OpenAPI/Swagger: <http://127.0.0.1:8000/docs>

Essas portas são diferentes das do frontend no Compose, que publica `8080`.

## Primeiro Fluxo

Depois de logar como admin demo, valide Dashboard, Medicamentos, Checagem,
Importações, Relatórios, Protocolos e IA. A jornada detalhada está em
`docs/product/first-run-user-journey.md`.
