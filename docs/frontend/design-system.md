# Design system healthtech

## Princípios

A interface é light-first e comunica segurança, evidência, revisão humana e rastreabilidade. Usa off-white, navy/slate, azul/teal clínico, verde suave, âmbar e vermelho controlado. Evita neon, glass pesado, estética “AI startup”, excesso de cards e clichês médicos.

## Tokens

Os tokens em `frontend/src/index.css` definem tipografia, cores semânticas, raios, elevação, foco e movimento. Controles têm 44 px ou mais, foco ciano de alto contraste e estados disabled/error distintos. `prefers-reduced-motion` reduz animações não essenciais.

## Componentes de domínio

- `PatientSummaryCard`, `MedicationSummary` e `ClinicalTimeline` dão contexto longitudinal;
- `ClinicalRiskBanner`, `CoverageIndicator` e `ClinicalDecisionCard` separam risco, cobertura e decisão;
- `EvidenceSourceCard` e `HumanReviewBadge` tornam fonte e revisão explícitas;
- `PharmacyInterventionCard` e `MedicationReconciliationPanel` mantêm proposta separada de aceite;
- `CohortAttrition` e `DataQualityFinding` tornam perdas e qualidade investigáveis;
- `ProtocolStatus`, `AIProposalBanner` e `AuditTimelineItem` deixam estado e autoridade visíveis.

## Conteúdo e imagens

Status brutos não aparecem em superfícies migradas. Imagens de runtime são locais, licenciadas, dimensionadas e acompanhadas de atribuição quando necessária; não há hotlink nem `img-src *`. Ilustrações SVG geométricas customizadas não compõem a identidade. Screenshots usam somente dados sintéticos.

## Limites

O sistema de design não certifica WCAG ou usabilidade clínica. Verificação automatizada é complementada por revisão visual e ainda requer testes formais com usuários antes de uso institucional.
