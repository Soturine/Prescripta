# Terminologia governada e adaptador OMOP v0.9.1

Consultado em 2026-08-11. Este documento separa contrato implementado, conteúdo fornecido pelo
operador e compatibilidade externa ainda não demonstrada.

## Decisão arquitetural

O Prescripta registra fonte, edição/release, checksum SHA-256, licença, jurisdição, proveniência e
estado de importação. Conceitos e mapeamentos são institucionais, versionados e imutáveis após
revisão. Busca textual produz sugestões; somente um mapeamento ativo, revisado por outra pessoa,
para conceito Standard e domínio compatível pode alimentar o adapter. Ambiguidade falha fechada.

O adapter implementa um subconjunto do OMOP CDM 5.4: `PERSON`, `VISIT_OCCURRENCE`,
`CONDITION_OCCURRENCE`, `DRUG_EXPOSURE`, `MEASUREMENT`, `PROCEDURE_OCCURRENCE` e `OBSERVATION`.
Ele preserva campos `*_source_value`, usa conceito 0 quando não há mapeamento e registra snapshot,
releases, hashes de mapping, métricas e arquivos CSV. É sintético/demo-only e não inclui as tabelas
completas de vocabulário, suporte, custos, provedores ou localização.

## Fontes primárias e licença

| Sistema | Uso no v0.9.1 | Limite explícito | Fonte oficial |
| --- | --- | --- | --- |
| OMOP CDM | contrato parcial v5.4; referência corrente v5.4.2 | não é CDM completo nem certificação | [OHDSI CommonDataModel v5.4.2](https://github.com/OHDSI/CommonDataModel/releases/tag/v5.4.2) |
| Standardized Vocabularies | metadados e subset fornecido pelo operador | Athena/full tables não são empacotados | [The Book of OHDSI — Standardized Vocabularies](https://ohdsi.github.io/TheBookOfOhdsi/StandardizedVocabularies.html) |
| SNOMED CT | metadados de fonte/release | conteúdo exige licença/território aplicável; nada é redistribuído | [SNOMED CT licensing](https://www.snomed.org/get-snomed) |
| LOINC | metadados e importação autorizada pelo operador | atribuição, versão e notices continuam obrigatórios | [LOINC license](https://loinc.org/license/) |
| RxNorm | metadados; RXCUI somente se vier do artefato registrado | distribuição completa/UMLS pode conter fontes com SRL própria | [RxNorm terms](https://www.nlm.nih.gov/research/umls/rxnorm/docs/termsofservice.html) |
| ICD | metadados com edição e jurisdição | não assumir equivalência entre ICD-10 nacionais e ICD-11; licença/mapping próprios | [WHO ICD licensing](https://www.who.int/standards/classifications/classification-of-diseases/licensing) |
| ATC/DDD | metadados e códigos fornecidos pelo operador | ATC não indica substituição terapêutica; copyright/licença aplicáveis | [WHOCC ATC/DDD](https://atcddd.fhi.no/) |

Nenhum conteúdo completo/licenciado desses sistemas entra em seed, teste ou release. Fixtures de
teste são pequenas, explicitamente sintéticas e não afirmam representar identificadores oficiais.

## Migração e rollback

1. Executar Alembic `d4b7c91a2e30` após backup.
2. Cadastrar a fonte e o release com licença/checksum antes do upload.
3. Importar somente CSV/ZIP-CSV autorizado; ZIP rejeita traversal, tipos inesperados e expansão
   excessiva.
4. Propor e revisar mappings com usuários distintos.
5. Gerar preview antes de exportar; comparar manifest e métricas.

O downgrade remove as novas tabelas e colunas v0.9.1. Isso perde registros terminológicos/exports;
por isso rollback de schema requer backup e janela explícita. Pacotes v0.9.0 existentes permanecem
imutáveis.

## Compatibilidade externa

| Alvo | Estado v0.9.1 |
| --- | --- |
| OMOP CDM 5.4 | adaptador parcial, sete tabelas |
| Athena/full vocabulary | loader de subset controlado, não bundle completo |
| DataQualityDashboard | não testado |
| Achilles/ATLAS | não suportado |
| estudo de rede OHDSI | não pronto |

O DQD suporta CDM 5.4, mas compatibilidade só poderá ser declarada depois de uma execução real e
evidenciada contra um CDM operacional. Consulte [The Book of OHDSI — Data Quality](https://ohdsi.github.io/TheBookOfOhdsi/DataQuality.html).
