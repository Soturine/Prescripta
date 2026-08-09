# Jornada inicial de uso

## Objetivo

Validar a demonstração com dados sintéticos e reconhecer a separação entre regras determinísticas, revisão humana e IA opcional.

## Opção A — Docker

1. Copie `.env.example` para `.env` e mantenha os valores de demonstração somente em ambiente local.
2. Execute `docker compose up --build`.
3. Aguarde PostgreSQL, migração, backend e frontend ficarem saudáveis.
4. Abra `http://127.0.0.1:8080`.

## Opção B — desenvolvimento nativo

1. Execute `scripts/setup-dev.ps1` e `scripts/check-install.ps1`.
2. Execute `scripts/dev.ps1`.
3. Abra `http://127.0.0.1:5173`.

## Percurso de produto

1. Entre com uma conta demonstrativa fornecida pelo seed local.
2. Escolha PT-BR ou EN-US e confirme os destinos permitidos no dashboard.
3. Abra um paciente sintético e revise alergias, medicamentos e contexto funcional.
4. Execute uma checagem e diferencie risco, cobertura, dados ausentes, fontes e explicação opcional.
5. Revise uma intervenção farmacêutica e uma importação item a item.
6. Explore evidências, um estudo sintético, attrition e proveniência.
7. Consulte o evento correspondente em Auditoria.

O [guia do usuário](../user-guide/README.md) detalha cada rota, permissão, dado persistido e limitação.

## Resultado esperado e limites

Ao final, deve estar claro que IA não decide risco, que uma proposta não é uma decisão e que um resultado RWE demonstrativo não constitui evidência clínica. Não use dados sensíveis reais nem credenciais de produção.
