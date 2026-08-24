# Quick Start

O caminho mais previsível para avaliação cross-platform é Docker. Para alterar o produto, use o
ambiente nativo no Windows. Em ambos os casos, use apenas dados sintéticos.

## Avaliar com Docker

Pré-requisito: Docker com Compose v2.

```bash
git clone https://github.com/Soturine/Prescripta.git
cd Prescripta
cp .env.example .env
docker compose up --build
```

- frontend: <http://localhost:8080>
- health da API: <http://localhost:8000/api/health>
- OpenAPI/Swagger: <http://localhost:8000/docs>

O serviço `migrate` executa `alembic upgrade head` antes do backend. Para parar preservando o banco,
use `docker compose down`; para remover também o volume demonstrativo, use
`docker compose down --volumes`.

## Desenvolver localmente no Windows

Pré-requisitos suportados no `main`: Python 3.12+, Node.js 22+ e npm 11.18.0. A CI de referência usa
Python 3.12 e Node.js 24.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-install.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

- frontend: <http://127.0.0.1:5173>
- health da API: <http://127.0.0.1:8000/api/health>
- OpenAPI/Swagger: <http://127.0.0.1:8000/docs>

`setup-dev.ps1` usa `npm install`, conforme sua implementação atual. Para uma instalação reprodutível
manual ou CI, use `npm ci` com o lockfile existente.

## Entrar na demonstração

Use `medico@prescripta.local` / `Medico@12345` para o percurso clínico ou consulte a
[tabela de perfis demo](../../README.md#primeiro-uso-e-perfis-demo). Essas credenciais são públicas e
servem somente ao seed local.

## Recriar o banco local

```powershell
powershell -ExecutionPolicy Bypass -File scripts/reset-demo-db.ps1
```

Esse script remove e recria somente `backend/prescripta.db`; ele não reseta o volume PostgreSQL do
Compose. Veja [setup local](../getting-started/local-setup.md), [Docker](../operations/docker.md) e
[troubleshooting](troubleshooting.md).
