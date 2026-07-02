# Comparacao Conceitual Com SafeDose

Data da revisao: 2026-07-02.

Esta comparacao usa o SafeDose/RicoToro apenas como benchmark conceitual. Nao houve copia de codigo, layout, textos, CSS, nomes internos, banco de dados ou estrutura.

Fonte publica observada: `https://github.com/RicoToro/SafeDose`. No momento da revisao, os metadados publicos indicavam descricao de aplicativo de saude com IA generativa para consultas e administracao de prontuarios, arvore com `.streamlit`, `.devcontainer`, `app.py`, `requirements.txt` e `README.md`, dependencias `streamlit`, `google-generativeai` e `cryptography`, README minimo, sem releases GitHub e sem workflows publicados.

## Criterios

| Criterio | Prescripta v0.3.0 | Classificacao |
| --- | --- | --- |
| Objetivo do produto | Apoio educacional a prescricao segura com regras explicitas e auditoria. | Melhor |
| Cadastro de pacientes | CRUD protegido por perfil, consumido por API real. | Melhor |
| Medicamentos | CRUD protegido e seed demonstrativo documentado. | Melhor |
| Checagem de alergia | Regra deterministica testada e auditada. | Melhor |
| Checagem de interacoes | Regras demonstrativas isoladas em service. | Melhor |
| Dose maxima | Calculo deterministico testado. | Melhor |
| Polifarmacia | Regra dedicada no motor de risco. | Melhor |
| Auditoria | Eventos com usuario, perfil, recurso, status e risco. | Melhor |
| Autenticacao | JWT, hash Argon2 e `/auth/me`. | Melhor |
| Perfis de usuario | `admin`, `medico`, `enfermagem` e `auditor` com rotas protegidas. | Melhor |
| Arquitetura frontend/backend | FastAPI separado de React; frontend consome API real. | Melhor |
| Testes | Pytest, Ruff, TypeScript e build validando a release. | Melhor |
| CI | Workflow de checks versionado desde v0.1.0. | Melhor |
| Documentacao | Arquitetura, seguranca, regras clinicas, releases, roadmap e benchmark. | Melhor |
| Release/tag/changelog | Tags `v0.1.0`, `v0.2.0`, changelog e release notes. | Melhor |
| Screenshots/GIF | Assets reais do app em `docs/assets/v0.3.0`. | Melhor |
| Seguranca | Threat model, roles, hashes, JWT e aviso de limites do MVP. | Melhor |
| Maturidade de portfolio | Projeto modular, testavel, documentado e publicavel. | Melhor |
| Clareza de escopo educacional | Avisos no README, API, docs e UI. | Melhor |
| Uso responsavel de IA | IA limitada a explicacao, com fallback e salvaguardas. | Melhor |

## Conclusao

Prescripta cobre as ideias centrais de um app de apoio em saude, mas apresenta uma execucao mais madura para portfolio: separacao clara entre backend e frontend, regras deterministicas testaveis, trilha de auditoria, controle de acesso, documentacao de seguranca e release management.

Ainda ha pendencias para v1.0, principalmente Docker/PostgreSQL, migracoes, deploy, logs estruturados e relatorios exportaveis. Mesmo assim, a v0.3.0 ja se posiciona acima de um prototipo monolitico Streamlit em modularidade, governanca, testabilidade e apresentacao publica.
