# Docker e Compose

Docker complementa o desenvolvimento nativo. O stack é uma demonstração local reproduzível, não um
deployment hospitalar validado.

## Quick start

```bash
git clone https://github.com/Soturine/Prescripta.git
cd Prescripta
cp .env.example .env
docker compose up --build
```

Abra o frontend em <http://localhost:8080>, a API em <http://localhost:8000/api/health> e a
documentação da API em <http://localhost:8000/docs>. PostgreSQL não publica porta no host.

O serviço `migrate` executa `alembic upgrade head` uma vez antes do backend. Réplicas da aplicação
não executam migration concorrentemente. O backend cria somente dados fictícios quando
`PRESCRIPTA_AUTO_SEED=true`; IA externa permanece desligada.

## Operação

```bash
docker compose ps
docker compose logs -f backend
docker compose run --rm migrate
docker compose down
docker compose down --volumes
```

O último comando remove o volume local e todos os dados demonstrativos do Compose. Para preservar o
banco entre reinícios, use apenas `docker compose down`.

## Segurança e runtime

- imagens oficiais possuem versão e digest OCI fixos;
- backend e frontend usam usuário sem privilégios, filesystem somente leitura, `/tmp` temporário,
  `cap_drop: ALL` e `no-new-privileges`;
- frontend contém apenas o build estático e Nginx, com SPA fallback, compressão e headers;
- secrets não entram na imagem; `.env` é ignorado e deve conter apenas valores locais nesta demo;
- readiness do backend depende do banco, nunca de OpenAI/Gemini/Ollama.

O perfil padrão não baixa modelo local. Ollama continua uma integração opcional externa ao Compose;
nenhum modelo é incorporado à imagem ou baixado no CI.

## Smoke e troubleshooting

`bash scripts/container-smoke.sh` valida Compose, builds, PostgreSQL, migration, health, restart e
usuários non-root. Ele não repete pytest, Vitest ou Playwright.

Se a porta estiver ocupada, altere `PRESCRIPTA_FRONTEND_PORT` ou `PRESCRIPTA_BACKEND_PORT`. Em falha
de banco, consulte `docker compose logs postgres migrate`. Uma falha de migration bloqueia o backend;
ela nunca é ignorada para deixar o container aparentemente saudável.
