# Historico Clinico, Laudos E Documentos

A v0.8.3 adiciona uma area longitudinal no paciente.

## Tipos Aceitos

- Texto colado.
- Documento PDF ou imagem como metadado/manual quando OCR nao estiver disponivel.
- CSV/JSON.
- FHIR Bundle.
- Laudo manual estruturado.

## Extracao Assistida

`ClinicalDocumentExtractor` usa provider ativo quando permitido e fallback
deterministico simples quando nao ha IA. Ele pode extrair medicamentos,
alergias, condicoes, exames, sintomas, eventos adversos, historico mental,
gravidez/lactacao e observacoes.

## Revisao Humana

Nada extraido vira dado validado automaticamente. O status inicial e
`pending_review`; um humano aceita ou rejeita entidades. Aceites entram na
timeline e no bundle do paciente.

## PatientKnowledgeBundle

O bundle minimiza dados antes de IA/relatorio/protocolo. Por padrao, nao envia
identificadores pessoais. Ele carrega apenas o necessario para o modulo.
