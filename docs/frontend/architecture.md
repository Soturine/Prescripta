# Arquitetura do frontend

## Estrutura

- `App.tsx` declara rotas e capacidades; `ProtectedRoute` melhora a experiência, mas o backend continua autoritativo;
- `components/Layout.tsx` compõe skip link, trilho desktop, cabeçalho, drawer e navegação móvel;
- `pages` organiza os workspaces por tarefa, sem regra clínica;
- `services` concentra contratos HTTP e React Query mantém estado remoto;
- `i18n` resolve locale e entrega catálogos estáticos;
- `components` contém superfícies de domínio, estados e controles reutilizáveis.

## Estado e fluxo

Entradas são validadas no formulário e reenviadas ao backend. Resultados clínicos exibem status, cobertura, fontes e auditoria retornados pela API. Nenhum componente recalcula severidade. A preferência de idioma é o único estado do redesign persistido localmente.

## Responsividade e acessibilidade

O layout parte de 320 px, mantém alvos mínimos de 44 px e muda de trilho para drawer/barra inferior. Tabelas críticas têm composição responsiva. Skip link, landmarks, foco visível, nomes acessíveis, teclado e `prefers-reduced-motion` fazem parte do contrato.

## Verificação

Lint, TypeScript estrito, Vitest, cobertura, build, Playwright, axe e screenshots versionados cobrem níveis diferentes. Mudança localizada usa teste focado; a suíte completa fica reservada ao release candidate.
