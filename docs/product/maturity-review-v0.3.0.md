# Revisao De Maturidade v0.3.0

Data: 2026-07-02.

## Perguntas

**O projeto parece maduro para portfolio?**
Sim. A v0.3.0 tem dominio separado, backend real, frontend consumindo API, testes, CI, releases, screenshots, GIF, changelog, roadmap e documentacao de seguranca.

**Esta mais completo que um prototipo Streamlit monolitico?**
Sim. Prescripta separa frontend, backend, services, schemas, repositories, dominio e documentacao. Isso deixa o projeto mais facil de testar, revisar e evoluir.

**A arquitetura esta bem separada?**
Sim. Regras ficam no backend, UI fica no React, persistencia fica em repositories e contratos ficam em schemas Pydantic/TypeScript.

**O backend e realmente a fonte das regras?**
Sim. O motor de risco e os verificadores determinam status, risco, alertas e recomendacao. O frontend apenas apresenta o resultado.

**O frontend esta consumindo API real?**
Sim. Axios e React Query chamam endpoints reais para login, dashboard, pacientes, medicamentos, checagem, auditoria, usuarios e explicacao.

**A auditoria esta boa?**
Boa para MVP. Ela registra checagens, usuario responsavel, acoes administrativas e metadados da explicacao de IA. Para v1.0, faltam filtros avancados, exportacao e politicas de retencao.

**Seguranca basica esta boa para MVP?**
Sim. Ha hash Argon2, JWT, roles no backend, threat model e aviso sobre `localStorage`. Para producao, ainda faltam cookies seguros, rotacao de segredo, revogacao, rate limit e hardening.

**IA esta limitada corretamente?**
Sim. Ela explica alertas existentes, funciona por clique, tem fallback deterministico, nao altera status/risco e preserva codigos criticos.

**O README vende bem o projeto?**
Sim. A v0.3.0 passa a destacar GIF, screenshots, IA explicativa, credenciais demonstrativas, links de maturidade e benchmark.

**O projeto passa impressao de healthtech seria?**
Sim, dentro do escopo educacional. A combinacao de motor deterministico, auditoria, seguranca, testes e avisos de uso responsavel comunica cuidado tecnico.

**O que ainda falta para v1.0?**

- Docker Compose;
- PostgreSQL e migracoes;
- filtros e exportacao de auditoria;
- relatorios PDF;
- logs estruturados;
- observabilidade;
- seeds revisados por especialista;
- deploy demonstrativo;
- politicas de privacidade e retencao mais detalhadas;
- hardening de sessao e segredo;
- testes end-to-end automatizados.

## Conclusao

Prescripta v0.3.0 esta pronto como projeto de portfolio tecnico: original, modular, testavel, documentado e apresentavel. Ainda nao e produto clinico e nao deve ser usado em decisoes reais, mas demonstra com clareza uma base profissional de healthtech educacional.
