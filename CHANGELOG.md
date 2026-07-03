# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue Keep a Changelog e o versionamento segue SemVer quando aplicável.

## [Unreleased]

### Planned

- Docker, PostgreSQL, migrações e deploy demonstrativo.

## [0.4.0] - 2026-07-02

### Added

- Perfil clínico inteligente do paciente com condições renal, hepática, cardíaca, gastrointestinal, hipertensão, diabetes, gravidez/lactação, reações adversas e completude.
- Triagem rápida com preservação de histórico e auditoria.
- Metadados clínicos de medicamento: duração máxima, dose acumulada máxima, limites por condição, cautelas por órgão/sistema, efeitos adversos e grupo de alternativas.
- Regras determinísticas para dose acumulada, duração, cautela renal/hepática/gastrointestinal/cardiaca, cautela em idosos, reação adversa e perfil incompleto.
- Compatibilidade paciente–medicação com score demonstrativo, fatores considerados e justificativas.
- RAG clínico demonstrativo com base interna em Markdown e busca textual normalizada.
- Clinical Context Graph lógico em JSON e card no frontend.
- Alternativas terapêuticas avaliadas pelo motor de risco antes de aparecerem como opções para avaliação profissional.
- IA explicativa multi-provider com OpenAI/OpenAI-compatible/local configurável e fallback determinístico.
- Script Windows `scripts/start-prescripta.ps1`.
- Documentação clínica, RAG, dados, arquitetura, maturidade e release v0.4.0.

### Security

- A IA continua sem poder de alterar status, risco, bloqueio, dose, recomendação final ou auditoria.
- Base RAG marcada como demonstrativa e não clínica real.
- Auditoria registra triagem rápida e alterações relevantes de perfil clínico.

## [0.3.0] - 2026-07-02

### Added

- Endpoint `POST /api/prescriptions/explain` para explicar alertas já gerados pelo motor determinístico.
- Service `ai_explainer.py` com fallback determinístico sem chave de API.
- Configurações `PRESCRIPTA_AI_PROVIDER`, `PRESCRIPTA_AI_API_KEY` e `PRESCRIPTA_AI_MODEL`.
- Botão "Explicar com IA" e painel de explicação na tela de checagem.
- Auditoria de metadados para solicitações de explicação.
- Testes de fallback, permissão, preservação de status/risco e bloqueios críticos.
- Documentação de IA explicativa, benchmark SafeDose, revisão de maturidade e release v0.3.0.

### Security

- IA limitada a explicação educacional, sem poder de liberar prescrição.
- Fallback local quando provider externo estiver indisponível.
- Endpoint protegido pelos mesmos perfis da checagem de prescrição.
- Threat model atualizado com riscos de IA, chaves e uso indevido.

## [0.2.0] - 2026-07-02

### Added

- Autenticação JWT com endpoint de login e `/auth/me`.
- Usuários com perfis `admin`, `medico`, `enfermagem` e `auditor`.
- Hash de senha com Argon2.
- Proteção de rotas no backend por perfil.
- Tela de login, logout e sessão no frontend.
- Navegação baseada em perfil.
- Gestão de usuários para administradores.
- Auditoria genérica com usuário responsável, ação, recurso, status e risco.
- Testes de autenticação, autorização e auditoria com usuário.

### Security

- Documentação de `PRESCRIPTA_SECRET_KEY` e expiração de token.
- Registro explícito da limitação de `localStorage` no MVP demonstrativo.

## [0.1.0] - 2026-07-02

### Added

- Backend FastAPI com pacientes, medicamentos, dashboard, checagem de prescrição e auditoria.
- Motor de risco determinístico para alergia, dose máxima, interação medicamentosa, polifarmácia, idade, contraindicação e via.
- Seed demonstrativo de pacientes e medicamentos.
- Frontend React com dashboard, CRUD básico, checagem e auditoria.
- Testes automatizados para regras principais e endpoint de checagem.
- Documentação modular, GitHub Actions e instruções de execução.
