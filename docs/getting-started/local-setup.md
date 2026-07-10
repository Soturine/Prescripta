# Setup Local

## Caminho Recomendado

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-install.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

O script cria `.venv`, instala dependências do backend, executa `npm install` no
frontend e sobe backend/frontend em janelas separadas.

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
