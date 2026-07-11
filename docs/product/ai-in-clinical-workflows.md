# IA Em Fluxos Clinicos

IA no Prescripta e assistiva, modular e limitada por schema.

## Modulos

- Checagem: explica alertas, dados faltantes e perguntas de contexto.
- Relatorios: compoe narrativa a partir de evidencias.
- Protocolos: explica racional, execucao e limitacoes.
- Medicamentos: estrutura fonte fornecida e cria item pendente de curadoria.
- Paciente: resume historico revisado e extrai entidades de laudo.
- Auditoria: resume linha do tempo sem ocultar evento.

## Regras

- Nao decidir risco.
- Nao alterar dose, status, protocolo, bloqueio ou regra critica.
- Nao inventar fonte ou dado ausente.
- Retornar JSON validado.
- Acionar fallback se fonte, schema ou provider falhar.
- Usar bundle minimizado e sem dado identificavel por padrao.
