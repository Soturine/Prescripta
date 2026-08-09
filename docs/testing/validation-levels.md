# Níveis de validação

O Prescripta usa validação incremental para manter feedback rápido sem enfraquecer os gates de
release. O nível é escolhido pelo impacto da alteração, não pela quantidade de arquivos.

## Level 1 — focused

Executado após uma alteração pequena. Exemplos: teste do serviço alterado, Vitest do componente,
typecheck da superfície TypeScript, checker de links para documentação ou validação do Dockerfile.

## Level 2 — subsystem

Executado ao concluir um subsistema, como Research, Pharmacy, internacionalização, navegação ou
containers. Inclui os testes relacionados, lint/typecheck pertinente e um smoke do fluxo afetado.

## Level 3 — full local

Reservado ao fechamento de um bloco de risco elevado e ao release candidate. Reúne backend,
frontend, build, banco e fluxos críticos, mas não precisa reproduzir jobs já provados por um gate
equivalente e rastreável.

## Level 4 — release

Executado uma única vez sobre o candidato final: CI, Security, PostgreSQL, regressão visual,
acessibilidade, container smoke, image scan, release-readiness e SBOM. Tag e release exigem todos os
gates obrigatórios no mesmo SHA.

## Regras operacionais

- documentação isolada não dispara suíte de aplicação local;
- commits são agrupados antes de push para evitar matrizes obsoletas;
- mudança em runtime/container recebe smoke direcionado; mudança clínica recebe teste adversarial;
- threshold nunca é reduzido para acomodar regressão;
- o relatório do candidato registra os níveis realmente executados e seus resultados.
