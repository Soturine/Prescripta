# Comparação Conceitual Com SafeDose

Data da revisão: 2026-07-02.

Esta comparação usa o SafeDose/RicoToro apenas como benchmark conceitual. Não houve cópia de código, layout, textos, CSS, nomes internos, banco de dados ou estrutura.

Fonte pública observada: `https://github.com/RicoToro/SafeDose`. No momento da revisão, os metadados públicos indicavam descrição de aplicativo de saúde com IA generativa para consultas e administração de prontuários, árvore com `.streamlit`, `.devcontainer`, `app.py`, `requirements.txt` e `README.md`, dependências `streamlit`, `google-generativeai` e `cryptography`, README mínimo, sem releases GitHub e sem workflows publicados.

## Critérios

| Critério | Prescripta v0.4.0 | Classificação |
| --- | --- | --- |
| Objetivo do produto | Apoio educacional à prescrição segura com regras explícitas, perfil clínico e auditoria. | Melhor |
| Cadastro de pacientes | CRUD protegido por perfil, perfil clínico estruturado e triagem rápida auditada. | Melhor |
| Histórico clínico do paciente | Condições renal, hepática, cardíaca, gastrointestinal, hipertensão, diabetes, alergias, reações e medicamentos contínuos. | Melhor |
| Medicamentos | CRUD protegido com metadados de dose, duração, dose acumulada, cautelas por órgão e efeitos adversos. | Melhor |
| Dose diária | Cálculo determinístico testado. | Melhor |
| Dose acumulada | Estimativa por duração e limite acumulado demonstrativo. | Melhor |
| Duração de uso | Alertas quando a duração ultrapassa limite ou fica ausente para medicamento com limite. | Melhor |
| Efeito colateral por quadro clínico | Cruzamento demonstrativo de efeitos, órgãos e histórico do paciente. | Melhor |
| Órgãos envolvidos | Metabolização, eliminação, cautelas renal/hepática/cardíaca/gastrointestinal e cautela em idosos. | Melhor |
| Compatibilidade paciente-medicação | Score demonstrativo, fatores considerados, justificativas e necessidade de revisão. | Melhor |
| RAG interno | Base Markdown demonstrativa com busca textual normalizada. | Melhor |
| IA explicativa responsável | Multi-provider opcional, fallback determinístico e sem poder de alterar decisão. | Melhor |
| Alternativas terapêuticas | Opções cadastradas avaliadas pelo motor de risco antes de aparecerem. | Melhor |
| Autenticação | JWT, hash Argon2 e `/auth/me`. | Melhor |
| Perfis de usuário | `admin`, `medico`, `enfermagem` e `auditor` com rotas protegidas. | Melhor |
| Auditoria | Eventos com usuário, perfil, recurso, status, risco e triagem rápida. | Melhor |
| Arquitetura frontend/backend | FastAPI separado de React; frontend consome API real. | Melhor |
| Testes | Pytest, Ruff, TypeScript e build validando a release. | Melhor |
| CI | Workflow de checks versionado desde v0.1.0. | Melhor |
| Documentação | Arquitetura, segurança, regras clínicas, IA, RAG, releases, roadmap e benchmark. | Melhor |
| Release/tag/changelog | Tags, changelog e release notes versionadas. | Melhor |
| Screenshots/GIF | Assets reais do app em `docs/assets/v0.4.0`. | Melhor |
| Segurança | Threat model, roles, hashes, JWT, limites da IA e aviso educacional. | Melhor |
| Maturidade de portfólio | Projeto modular, testável, documentado e publicável. | Melhor |

## Conclusão

Prescripta cobre as ideias centrais de um app de apoio em saúde, mas apresenta uma execução mais madura para portfólio: separação clara entre backend e frontend, regras determinísticas testáveis, trilha de auditoria, controle de acesso, documentação de segurança, RAG demonstrativo, IA responsável e release management.

Ainda há pendências para v1.0, principalmente Docker/PostgreSQL, migrações, deploy, logs estruturados, relatórios exportáveis e validação clínica da base demonstrativa. Mesmo assim, a v0.4.0 já se posiciona acima de um protótipo monolítico Streamlit em modularidade, governança, testabilidade e apresentação pública.
