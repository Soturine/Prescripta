# IA Em Fluxos Clínicos

IA no Prescripta e assistiva, modular e limitada por schema.

## Modulos

- Checagem: explica alertas, dados faltantes e perguntas de contexto.
- Relatórios: compoe narrativa a partir de evidencias.
- Protocolos: explica racional, execução e limitacoes.
- Medicamentos: estrutura fonte fornecida e cria item pendente de curadoria.
- Paciente: resume histórico revisado e extrai entidades de laudo.
- Auditoria: resume linha do tempo sem ocultar evento.

## Regras

- Não decidir risco.
- Não alterar dose, status, protocolo, bloqueio ou regra critica.
- Não inventar fonte ou dado ausente.
- Retornar JSON validado.
- Acionar fallback se fonte, schema ou provider falhar.
- Usar bundle minimizado e sem dado identificável por padrão.
