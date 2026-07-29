# Clinical safety hazard log

Registro demonstrativo de perigos. Severidade descreve dano potencial, não probabilidade observada.
Nenhum item foi avaliado por comitê clínico externo.

| ID | Perigo | Severidade | Controle/evidência | Estado residual |
| --- | --- | --- | --- | --- |
| H-01 | resultado favorável apesar de achado crítico | catastrófica | precedência canônica, invariantes e teste `test_critical_psychotropic_signal_blocks_aggregate_decision` | reduzido tecnicamente; validação clínica externa pendente |
| H-02 | falsa segurança por regra/fonte ausente | maior | `coverage_status`, abstention, dados faltantes e teste de false green | catálogo continua incompleto/demo |
| H-03 | erro de unidade ou frequência em dose | catastrófica | contrato dimensional, conversão mg/mcg/g e abstention para dimensão incompatível | rulesets não são clinicamente aprovados |
| H-04 | fórmula corporal usa sexo imputado | maior | input explícito e abstention quando ausente | sexo biológico/contexto clínico requer governança cuidadosa |
| H-05 | cliente altera regra, limite ou decisão | catastrófica | CDS resolve catálogo no servidor; explicação usa `audit_id` e snapshot | superfícies futuras precisam manter o contrato |
| H-06 | relatório histórico muda com cadastro | maior | snapshot imutável, hash canônico, relatório snapshot-only | falta assinatura/WORM externa |
| H-07 | decisão parcial é persistida sem auditoria | maior | unit of work, flush/commit único e teste de rollback | integração distribuída exigiria outbox/coordenação |
| H-08 | usuário acessa paciente de outra instituição | maior | grants/tenant scope e testes BOLA negativos | modelo institucional demo não representa organizações reais |
| H-09 | override apaga alerta ou reduz severidade | catastrófica | entidade separada, crítico/hard block não admite override, coassinatura independente | efetividade da policy depende de instituição real |
| H-10 | IA inventa conduta ou reduz risco | catastrófica | IA explicativa, payload allowlisted, source locking, validação de resposta e fallback | avaliação formal de prompt injection/groundedness pendente |
| H-11 | regra ou fonte expirada continua favorável | maior | validade no índice e `SOURCE_EXPIRED` impede decisão favorável | metadados históricos ainda são demo/incompletos |
| H-12 | enfermagem é bloqueada ou liberada genericamente | maior | policy distingue papel e protocolo; documentação usa COFEN 801/2026 | cadastro completo de protocolo/COREN/serviço não foi implementado |

## Critério de liberação

Nenhuma severidade deste log autoriza uso real. Uso clínico exigiria, no mínimo, hazard analysis
formal, gestão de risco, validação de rulesets e doses por especialistas, teste de usabilidade com
profissionais, piloto controlado, monitoramento pós-implantação e enquadramento regulatório.
