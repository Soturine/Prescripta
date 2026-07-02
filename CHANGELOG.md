# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue Keep a Changelog e o versionamento segue SemVer quando aplicável.

## [Unreleased]

### Planned

- Autenticação e perfis de usuário.
- Camada futura de IA explicativa para alertas já determinados por regras.
- Exportação de relatórios.

## [0.1.0] - 2026-07-02

### Added

- Backend FastAPI com pacientes, medicamentos, dashboard, checagem de prescrição e auditoria.
- Motor de risco determinístico para alergia, dose máxima, interação medicamentosa, polifarmácia, idade, contraindicação e via.
- Seed demonstrativo de pacientes e medicamentos.
- Frontend React com dashboard, CRUD básico, checagem e auditoria.
- Testes automatizados para regras principais e endpoint de checagem.
- Documentação modular, GitHub Actions e instruções de execução.
