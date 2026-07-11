# Fluxos Clinicos

## Checagem De Prescri??o

1. Selecione paciente e medicamento.
2. Informe dose, frequencia, via e duracao.
3. O backend monta `PrescriptionContextBundle` e `PatientKnowledgeBundle`.
4. O motor calcula alertas deterministicos.
5. A UI mostra visao clinica por padrao.
6. Relatorios e IA explicativa podem ser acionados sem alterar decis?o.

## Hist?rico Do Paciente

O hist?rico longitudinal une documentos revisados, observacoes, medicamentos
anteriores, importacoes aceitas, perfil funcional e eventos de protocolo.

## Protocolos

Protocolos sao versionados. Cada execu??o guarda protocolo, versao, contexto,
passos, calculos, paciente selecionado, flags e relat?rio gerado.

## Relatorios

Relatorios usam bundles fechados, hash e metadados de IA/fallback. A narrativa
pode ser assistida por IA, mas o conteudo decisorio vem do backend.
