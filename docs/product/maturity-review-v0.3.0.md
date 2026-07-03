# Revisão De Maturidade v0.3.0

Data: 2026-07-02.

> Nota: a v0.4.0 supersede esta revisão ao adicionar perfil clínico inteligente, dose acumulada, RAG interno e alternativas avaliadas. Este documento permanece como registro histórico da release v0.3.0.

## Perguntas

**O projeto parece maduro para portfólio?**
Sim. A v0.3.0 tem domínio separado, backend real, frontend consumindo API, testes, CI, releases, screenshots, GIF, changelog, roadmap e documentação de segurança.

**Está mais completo que um protótipo Streamlit monolítico?**
Sim. Prescripta separa frontend, backend, services, schemas, repositories, domínio e documentação. Isso deixa o projeto mais fácil de testar, revisar e evoluir.

**A arquitetura está bem separada?**
Sim. Regras ficam no backend, UI fica no React, persistência fica em repositories e contratos ficam em schemas Pydantic/TypeScript.

**O backend é realmente a fonte das regras?**
Sim. O motor de risco e os verificadores determinam status, risco, alertas e recomendação. O frontend apenas apresenta o resultado.

**O frontend está consumindo API real?**
Sim. Axios e React Query chamam endpoints reais para login, dashboard, pacientes, medicamentos, checagem, auditoria, usuários e explicação.

**A auditoria está boa?**
Boa para MVP. Ela registra checagens, usuário responsável, ações administrativas e metadados da explicação de IA. Para v1.0, faltam filtros avançados, exportação e políticas de retenção.

**Segurança básica está boa para MVP?**
Sim. Há hash Argon2, JWT, roles no backend, threat model e aviso sobre `localStorage`. Para produção, ainda faltam cookies seguros, rotação de segredo, revogação, rate limit e hardening.

**IA está limitada corretamente?**
Sim. Ela explica alertas existentes, funciona por clique, tem fallback determinístico, não altera status/risco e preserva códigos críticos.

**O README vende bem o projeto?**
Sim. A v0.3.0 passa a destacar GIF, screenshots, IA explicativa, credenciais demonstrativas, links de maturidade e benchmark.

**O projeto passa impressão de healthtech séria?**
Sim, dentro do escopo educacional. A combinação de motor determinístico, auditoria, segurança, testes e avisos de uso responsável comunica cuidado técnico.

**O que ainda falta para v1.0?**

- Docker Compose;
- PostgreSQL e migrações;
- filtros e exportação de auditoria;
- relatórios PDF;
- logs estruturados;
- observabilidade;
- seeds revisados por especialista;
- deploy demonstrativo;
- políticas de privacidade e retenção mais detalhadas;
- hardening de sessão e segredo;
- testes end-to-end automatizados.

## Conclusão

Prescripta v0.3.0 está pronto como projeto de portfólio técnico: original, modular, testável, documentado e apresentável. Ainda não é produto clínico e não deve ser usado em decisões reais, mas demonstra com clareza uma base profissional de healthtech educacional.
