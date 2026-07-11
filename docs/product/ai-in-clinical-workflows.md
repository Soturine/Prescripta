# IA Em Fluxos Clinicos

IA no Prescripta e assistiva, modular e limitada por schema.

## Modulos

- Checagem: explica alertas, dados faltantes e perguntas de contexto.
- Relatorios: compoe narrativa a partir de evidencias.
- Protocolos: explica racional, execu??o e limitacoes.
- Medicamentos: estrutura fonte fornecida e cria item pendente de curadoria.
- Paciente: resume hist?rico revisado e extrai entidades de laudo.
- Auditoria: resume linha do tempo sem ocultar evento.

## Regras

- N?o decidir risco.
- N?o alterar dose, status, protocolo, bloqueio ou regra critica.
- N?o inventar fonte ou dado ausente.
- Retornar JSON validado.
- Acionar fallback se fonte, schema ou provider falhar.
- Usar bundle minimizado e sem dado identificavel por padrao.
