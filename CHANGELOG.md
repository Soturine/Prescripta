# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue Keep a Changelog e o versionamento segue SemVer quando aplicável.

## [Unreleased]

### Planned

- Camada futura de IA explicativa para alertas já determinados por regras.
- Exportação de relatórios.

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
