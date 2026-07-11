# Guia para médicos

## Leitura da checagem

A checagem consolida dose/rota/duração, alergias, medicamentos concomitantes, comorbidades,
condição renal/hepática/cardíaca, idade, antropometria, fatores neuropsiquiátricos e reprodutivos,
perfil funcional, histórico e laudos revisados. Dados ausentes aparecem explicitamente; não são
interpretados como negativos.

Alertas são achados determinísticos. Bloqueio é reservado ao motor de risco/política com fundamento
registrado. `requires_human_review` indica incerteza, regra demo, credencial incompleta ou cautela.
Dose Intelligence mostra fórmula e faixa, mas não seleciona dose. Sinais psicotrópicos descrevem
mecanismo e associação sem diagnosticar síndrome serotoninérgica, mania ou toxicidade.

## Especialidade e política

Especialidade, CRM e RQE são fictícios e não verificados. Leia `policy_type`: legal/regulatória
requer fonte oficial; institucional pertence ao serviço; recomendação clínica sugere revisão; demo é
exemplo. Metadona ou anestésicos podem exigir revisão especializada demo sem que isso declare uma
restrição legal nacional.

Use a visão técnica para conferir regra, unidade, versão, fonte e JSON. Relatórios preservam o
EvidenceBundle e o fallback. Evite falsa segurança: confirme anamnese, exame, laboratório, bula,
norma vigente, protocolo local e aplicabilidade individual antes de decidir.

## Passo a passo recomendado

1. confirme identidade fictícia e completude do perfil;
2. revise documento pendente antes de incorporá-lo;
3. informe dose por administração, frequência, via e duração sem converter unidade mentalmente;
4. leia dados faltantes antes dos alertas;
5. confira fórmula/fonte da dose e vigência da policy;
6. registre revisão e gere relatório somente quando o bundle representar o caso.

## O que não significa

`within_usual_range` não significa dose indicada; `allowed` não significa autorização legal;
ausência de sinal não exclui interação; score de compatibilidade não é probabilidade clínica.

## Perguntas frequentes

**Por que a regra não calculou?** Fonte, unidade ou antropometria podem faltar. **Policy demo
bloqueia?** Ela exige revisão, não cria lei. **Posso confiar em documento extraído?** Apenas após
revisão humana.

## Glossário e links

Dose por administração difere de dose diária e cumulativa. Veja [motor de dose](../clinical/dose-intelligence-engine.md),
[psicotrópicos](../clinical/psychotropic-safety-engine.md) e [policy](../clinical/prescriber-policy-engine.md).
