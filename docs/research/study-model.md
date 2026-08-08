# Modelo de estudo Research/RWE

O vertical slice da v0.8.8 cobre um ciclo demonstrativo completo: estudo, versão de
protocolo, concept set, coorte declarativa, outcome e execução determinística. Todos os
recursos são institucionais e usam UUID, autoria, revisão e hashes canônicos.

`ResearchStudy` é o contêiner mutável. O conteúdo metodológico vive em
`StudyProtocolVersion`; depois de `reviewed_demo`, campos de definição não podem ser
alterados. Uma mudança exige nova versão. Os designs aceitos nesta versão são
`retrospective_cohort`, `cross_sectional` e `descriptive`. Não há inferência causal.

Cada `CohortRun` registra versão do protocolo e da coorte, marcador do dataset, fontes,
engine, versão do Prescripta, attrition, agregados e hash do run. O
`ResearchSnapshot` preserva a entrada e o resultado aggregate-first sem identificadores
de pacientes.

> Research/RWE nesta versão opera exclusivamente sobre dados sintéticos/demonstrativos
> e não produz evidência válida para tomada de decisão clínica.
