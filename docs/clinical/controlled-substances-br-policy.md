# Política brasileira de substâncias controladas

A Anvisa mantém e atualiza a lista de substâncias sujeitas a controle especial associada à
Portaria SVS/MS nº 344/1998. Como a versão vigente pode mudar, lista, tipo de notificação, fonte,
data e jurisdição devem ser dados versionados, nunca constantes presumidas.

O Prescripta modela `controlled_substance_list` e `prescription_form_type`, mas sementes são
demonstrativas e pendentes de revisão. O Código de Ética Médica exige cuidado com especialidade
anunciada e registro correspondente; isso justifica modelar CRM/RQE com segurança, não consultar
ou validar registros nesta versão.

O sistema não substitui farmacêutico, médico, assessoria jurídica, Anvisa, vigilância sanitária ou
política institucional. Sem fonte oficial clara, uma restrição é `demo_policy`,
`institutional_policy` ou `clinical_recommendation`, nunca bloqueio legal.
