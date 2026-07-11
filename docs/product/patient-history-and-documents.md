# Histórico Clínico, Laudos E Documentos

A v0.8.3 adiciona uma area longitudinal no paciente.

## Tipos Aceitos

- Texto colado.
- Documento PDF ou imagem como metadado/manual quando OCR não estiver disponivel.
- CSV/JSON.
- FHIR Bundle.
- Laudo manual estruturado.

## Extração Assistida

`ClinicalDocumentExtractor` usa provider ativo quando permitido e fallback
deterministico simples quando não ha IA. Ele pode extrair medicamentos,
alergias, condições, exames, sintomas, eventos adversos, histórico mental,
gravidez/lactacao e observacoes.

## Revisão Humana

Nada extraido vira dado validado automaticamente. O status inicial e
`pending_review`; um humano aceita ou rejeita entidades. Aceites entram na
timeline e no bundle do paciente.

## PatientKnowledgeBundle

O bundle minimiza dados antes de IA/relatório/protocolo. Por padrão, não envia
identificadores pessoais. Ele carrega apenas o necessario para o módulo.
