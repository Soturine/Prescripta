# Fluxos Clinicos

## Checagem De Prescrição

1. Selecione paciente e medicamento.
2. Informe dose, frequencia, via e duracao.
3. O backend monta `PrescriptionContextBundle` e `PatientKnowledgeBundle`.
4. O motor calcula alertas deterministicos.
5. A UI mostra visao clinica por padrao.
6. Relatorios e IA explicativa podem ser acionados sem alterar decisão.

## Histórico Do Paciente

O histórico longitudinal une documentos revisados, observacoes, medicamentos
anteriores, importacoes aceitas, perfil funcional e eventos de protocolo.

## Protocolos

Protocolos sao versionados. Cada execução guarda protocolo, versao, contexto,
passos, calculos, paciente selecionado, flags e relatório gerado.

## Relatorios

Relatorios usam bundles fechados, hash e metadados de IA/fallback. A narrativa
pode ser assistida por IA, mas o conteudo decisorio vem do backend.
