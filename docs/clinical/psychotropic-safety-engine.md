# Psychotropic Safety Engine

## Escopo

O motor produz sinais de risco para revisão, não diagnóstico. Cruza medicamento novo, lista atual,
classes, fatores neuropsiquiátricos, rim/fígado, gestação, idade, álcool e atividades de risco.
Cada `PsychotropicRiskSignal` registra código, severidade determinística, mecanismo, medicamentos,
fatores, dados faltantes, recomendação, fontes, status e revisão humana.

## Taxonomia e sinais

A taxonomia cobre ISRS, IRSN, tricíclicos, IMAO, antipsicóticos, estabilizadores, lítio, valproato,
carbamazepina, lamotrigina, benzodiazepínicos, Z-drugs, estimulantes, opioides, gabapentinoides,
cetamina, anticolinérgicos e sedativos. Exemplos: IMAO com antidepressivo serotoninérgico;
tramadol/linezolida com ISRS; antidepressivo com bipolaridade; estimulante com mania/psicose;
bupropiona com convulsão ou transtorno alimentar; benzodiazepínico com opioide/álcool; metadona e
QT; lítio com rim/AINE/IECA/BRA/diurético; valproato e gestação; carbamazepina e contraceptivo.

Ausência de história de mania diante de antidepressivo gera pergunta mínima. O sinal informa que
síndrome serotoninérgica, toxicidade ou descompensação são riscos a revisar — nunca afirma que o
paciente apresenta a condição.

## Governança

Regras são versionadas, usam fontes identificáveis e começam como `demo_seed` ou
`pending_review`. IA apenas resume evidência recuperada; não pode mudar código, severidade ou
recomendação determinística.
