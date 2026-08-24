# Troubleshooting

## Python, Node ou npm não encontrados

- confirme `python --version`, `node --version` e `npm --version`;
- o backend requer Python 3.12+; o frontend declara Node.js 22+ e npm 11.18.0;
- a CI de referência usa Python 3.12 e Node.js 24;
- no Windows, reabra o terminal depois de instalar ou alterar o `PATH`.

## Instalação frontend falha

Para reproduzir o lockfile, execute:

```powershell
cd frontend
npm ci
```

O `scripts/setup-dev.ps1` usa `npm install` por implementação. Não apague ou regenere o lockfile para
contornar um erro; confira a versão do runtime e a mensagem do install script.

## Porta ocupada

- desenvolvimento local: frontend `5173`, backend `8000`;
- Compose: frontend `8080`, backend `8000`.

Passe outras portas ao script local quando necessário:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 -BackendPort 8010 -FrontendPort 5174
```

No Compose, defina `PRESCRIPTA_BACKEND_PORT` e `PRESCRIPTA_FRONTEND_PORT` no `.env` e ajuste
`VITE_API_URL`/CORS de forma correspondente.

## Docker daemon parado ou stack não saudável

```bash
docker version
docker compose ps
docker compose logs backend
docker compose logs migrate
```

Abra Docker Desktop ou inicie o daemon antes de repetir `docker compose up --build`. PostgreSQL não
publica porta no host; o backend depende do término bem-sucedido do serviço `migrate`.

## Banco ou migration falha

No Compose, consulte `docker compose logs migrate` e execute novamente a migration one-shot:

```bash
docker compose run --rm migrate
```

Para descartar somente os dados demonstrativos do Compose, use `docker compose down --volumes`. Para
SQLite local, use `scripts/reset-demo-db.ps1`; esse script não altera o volume PostgreSQL.

## Health ou frontend não alcança a API

- local: <http://127.0.0.1:8000/api/health> e `VITE_API_URL=http://127.0.0.1:8000/api`;
- Compose: <http://localhost:8000/api/health> e frontend em <http://localhost:8080>;
- confira `PRESCRIPTA_CORS_ORIGINS` quando mudar portas;
- valide `.env` contra `.env.example` sem publicar seu conteúdo.

## Login demo falha

- confirme `PRESCRIPTA_AUTO_SEED=true` no ambiente local;
- use somente uma conta da [tabela pública de perfis demo](../../README.md#primeiro-uso-e-perfis-demo);
- no SQLite local, execute `scripts/reset-demo-db.ps1` para recriar o seed;
- no Compose, recrie o volume apenas se puder perder todos os dados demonstrativos.

## IA externa indisponível

IA externa não é requisito para a demo. Mantenha `PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS=false` e use o
fallback determinístico. Apenas admin pode configurar, testar ou ativar provider/modelo; nunca coloque
API key em documentação, log ou `localStorage`.

## Playwright, Chromium ou ffmpeg ausentes

Esses componentes são necessários para E2E/captura, não para uso normal do produto. Instale o browser
do Playwright no frontend com `npx playwright install chromium`. Instale `ffmpeg` somente se for gerar
o GIF por `scripts/capture-current-assets.mjs`.

## PDF com caracteres estranhos

O renderer simples normaliza caracteres para o conjunto suportado. Registre o texto que falhou; não
altere código durante uma rodada documental.

## Protocolos não executam

- perfis de auditoria podem consultar, mas não registrar execução;
- preencha os campos obrigatórios e confirme a capacidade da sessão;
- protocolos são demonstrativos e sempre exigem decisão humana.
