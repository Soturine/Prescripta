# Dashboard

## Objetivo e acesso

Apresentar uma visão operacional inicial e atalhos coerentes com o perfil. Requer `dashboard.view` e dados carregados no ambiente.

## Seções e passos

1. Leia os indicadores de pacientes, checagens e alertas.
2. Observe severidade e contexto antes de abrir um item.
3. Use os atalhos de domínio para continuar em pacientes, prescrição, evidência ou auditoria.
4. Atualize a página se um indicador estiver defasado após uma operação recente.

## Exemplo e erros comuns

Um aumento de alertas críticos orienta a priorização da fila, mas não prova incidente clínico. Estado vazio pode significar base nova ou filtro de escopo. Erro de carregamento não deve ser interpretado como zero.

## Dados, auditoria, IA e autoridade

Os indicadores são agregações de dados persistidos pelo backend; abrir um atalho não muda o estado clínico. Ações subjacentes permanecem auditáveis. A IA não calcula contagens nem severidade. Os registros de origem e as regras determinísticas são autoritativos.

## Limitações

O dashboard é um resumo, não uma fila assistencial completa nem substituto da revisão do paciente e do evento de auditoria.
