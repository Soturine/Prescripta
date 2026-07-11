# Guia para leigos e avaliadores

## Conceitos básicos

Prescrição é a orientação profissional sobre um tratamento. Princípio ativo é a substância que
produz o efeito; um nome comercial pode conter o mesmo princípio. Dose diária soma todas as
administrações do dia. Dose por peso multiplica uma regra em mg/kg pelo peso aplicável. IMC relaciona
peso e altura; superfície corporal é outra medida usada em contextos específicos.

Medicamento controlado segue requisitos sanitários próprios. Psicotrópico atua no sistema nervoso e
pode exigir cautelas de interação, sedação ou monitoramento. Protocolo organiza etapas previamente
aprovadas. Auditoria registra quem fez o quê, quando e com qual evidência. IA assistiva explica ou
extrai texto; não toma a decisão.

## Exemplo do começo ao fim

Um usuário entra com conta demo, escolhe um paciente fictício e informa medicamento, dose, via e
duração. O backend considera alergias, medicamentos atuais, condições, idade, peso, altura e dados
faltantes. Em seguida apresenta resultado geral, cálculo de dose, sinais psicotrópicos, política do
prescritor, fontes e perguntas de revisão. O profissional revisa; a checagem e o relatório ficam
auditados com hash.

O sistema não diagnostica, prescreve sozinho, confirma CRM/RQE, consulta hospitais ou garante que
uma dose é adequada. Um cartão verde não representa segurança clínica absoluta: depende da
qualidade dos dados e das regras cadastradas.
