# Pesquisa e RWE

## Objetivo e acesso

O workspace organiza estudos observacionais reprodutíveis sem transformar exploração em recomendação clínica. A rota requer `research.study.read`; capacidades específicas controlam criação, execução e exportação.

## Fluxo recomendado

1. Defina o [estudo](studies.md) e a pergunta.
2. Construa [coortes](cohorts.md) e [concept sets](concept-sets.md) versionados.
3. Especifique [desfechos](outcomes.md), janelas e análises.
4. Execute e acompanhe [runs](runs.md).
5. Revise [qualidade dos dados](data-quality.md) e [proveniência](provenance.md).

## Exemplo e erros comuns

Um estudo sintético de utilização de medicamentos pode comparar coortes com critérios explícitos. Uma execução concluída não valida causalidade, e uma amostra grande não corrige viés de seleção.

## Dados, auditoria, IA e autoridade

Definições, versões, execuções e artefatos são persistidos e auditados. A IA pode auxiliar na redação ou classificação sobre dados fornecidos, mas não define elegibilidade, desfecho ou conclusão. A especificação versionada, os dados de origem e os resultados computados são autoritativos.

## Limitações

O módulo não substitui protocolo científico, revisão ética, governança de dados ou validação estatística independente.
