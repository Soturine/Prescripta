# Hist?rico Cl?nico, Laudos E Documentos

A v0.8.3 adiciona uma area longitudinal no paciente.

## Tipos Aceitos

- Texto colado.
- Documento PDF ou imagem como metadado/manual quando OCR n?o estiver disponivel.
- CSV/JSON.
- FHIR Bundle.
- Laudo manual estruturado.

## Extracao Assistida

`ClinicalDocumentExtractor` usa provider ativo quando permitido e fallback
deterministico simples quando n?o ha IA. Ele pode extrair medicamentos,
alergias, condicoes, exames, sintomas, eventos adversos, hist?rico mental,
gravidez/lactacao e observacoes.

## Revis?o Humana

Nada extraido vira dado validado automaticamente. O status inicial e
`pending_review`; um humano aceita ou rejeita entidades. Aceites entram na
timeline e no bundle do paciente.

## PatientKnowledgeBundle

O bundle minimiza dados antes de IA/relat?rio/protocolo. Por padrao, n?o envia
identificadores pessoais. Ele carrega apenas o necessario para o modulo.
