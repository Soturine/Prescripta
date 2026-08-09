# Clinical safety hazard log

Registro demonstrativo de perigos. Severidade descreve dano potencial, não probabilidade observada.
Nenhum item foi avaliado por comitê clínico externo.

| ID | Perigo | Severidade | Controle/evidência | Estado residual |
| --- | --- | --- | --- | --- |
| H-01 | resultado favorável apesar de achado crítico | catastrófica | precedência canônica, invariantes e teste `test_critical_psychotropic_signal_blocks_aggregate_decision` | reduzido tecnicamente; validação clínica externa pendente |
| H-02 | falsa segurança por regra/fonte ausente | maior | `coverage_status`, abstention, dados faltantes e teste de false green | catálogo continua incompleto/demo |
| H-03 | erro de unidade, concentração, frequência ou taxa em dose | catastrófica | quantidades dimensionais exatas, concentração × volume, intervalo, PRN/taxa separados, rounding rastreado e abstention adversarial | rulesets não são clinicamente aprovados |
| H-04 | fórmula corporal usa sexo imputado | maior | input explícito e abstention quando ausente | sexo biológico/contexto clínico requer governança cuidadosa |
| H-05 | cliente altera regra, limite ou decisão | catastrófica | CDS resolve catálogo no servidor; explicação usa `audit_id` e snapshot | superfícies futuras precisam manter o contrato |
| H-06 | relatório histórico muda com cadastro | maior | snapshot imutável, hash canônico, relatório snapshot-only | falta assinatura/WORM externa |
| H-07 | decisão parcial é persistida sem auditoria | maior | unit of work, flush/commit único e teste de rollback | integração distribuída exigiria outbox/coordenação |
| H-08 | usuário acessa paciente sem relação, inclusive no mesmo tenant | maior | capability + relação/purpose, scoping no banco, break-glass governado e testes same/cross-tenant | modelo institucional demo não representa organizações reais |
| H-09 | override apaga alerta ou reduz severidade | catastrófica | entidade separada, crítico/hard block não admite override, coassinatura independente | efetividade da policy depende de instituição real |
| H-10 | IA inventa conduta ou reduz risco | catastrófica | IA explicativa, payload allowlisted, source locking, validação de resposta e fallback | avaliação formal de prompt injection/groundedness pendente |
| H-11 | regra ou fonte expirada continua favorável | maior | validade no índice e `SOURCE_EXPIRED` impede decisão favorável | metadados históricos ainda são demo/incompletos |
| H-12 | enfermagem é bloqueada ou liberada genericamente | maior | protocolo institucional versionado verifica capacidade, vínculo, profissão, credencial, região, fonte, revisão, vigência, escopo e coassinatura | conteúdo/credencial seed não foi validado por conselho ou instituição real |
| H-13 | contexto psicológico é exposto por grant clínico amplo | maior | segmento e capacidades psicológicas separados; testes de perfil e objeto | taxonomia/consentimento institucional exigem validação externa |
| H-14 | intervenção farmacêutica altera prescrição sem decisão humana | catastrófica | workflow separado, estado/versionamento/eventos e aviso de que nenhuma alteração é automática | integração de dispensação real não implementada nem validada |
| H-15 | IA executa ou publica coorte/protocolo inventado | maior | Task Router proposal-only, schema/DSL/source IDs validados, `needs_review` e ausência de escrita no domínio | avaliação formal de groundedness e prompt injection permanece externa |
| H-16 | resultado de RWE sintético é tratado como evidência clínica | maior | avisos persistentes, `demo_only`, aggregate-first, sem inferência causal e provenance completo | governança humana e barreiras organizacionais não podem ser garantidas pelo código |
| H-17 | erro de coorte fica oculto pela contagem final | maior | attrition por critério, definition/run hashes, marcador do dataset e Data Quality determinística | validação epidemiológica de fenótipos e fontes reais pendente |
| H-18 | tradução altera a interpretação de risco, status, unidade ou código clínico | catastrófica | catálogos estáticos revisáveis, valores canônicos preservados, units/codes não traduzidos, testes de equivalência PT-BR/EN-US e fallback PT-BR | revisão linguística clínica formal e validação com usuários bilíngues pendem |

## Critério de liberação

Nenhuma severidade deste log autoriza uso real. Uso clínico exigiria, no mínimo, hazard analysis
formal, gestão de risco, validação de rulesets e doses por especialistas, teste de usabilidade com
profissionais, piloto controlado, monitoramento pós-implantação e enquadramento regulatório.
