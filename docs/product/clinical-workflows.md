# Fluxos Clinicos

## Checagem De Prescricao

1. Selecione paciente e medicamento.
2. Informe dose, frequencia, via e duracao.
3. O backend monta `PrescriptionContextBundle` e `PatientKnowledgeBundle`.
4. O motor calcula alertas deterministicos.
5. A UI mostra visao clinica por padrao.
6. Relatorios e IA explicativa podem ser acionados sem alterar decisao.

## Historico Do Paciente

O historico longitudinal une documentos revisados, observacoes, medicamentos
anteriores, importacoes aceitas, perfil funcional e eventos de protocolo.

## Protocolos

Protocolos sao versionados. Cada execucao guarda protocolo, versao, contexto,
passos, calculos, paciente selecionado, flags e relatorio gerado.

## Relatorios

Relatorios usam bundles fechados, hash e metadados de IA/fallback. A narrativa
pode ser assistida por IA, mas o conteudo decisorio vem do backend.
