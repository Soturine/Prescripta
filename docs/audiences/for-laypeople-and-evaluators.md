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

## O que aparece na tela

O Dashboard resume volume e qualidade; Pacientes mostra o contexto; Medicamentos explica origem e
curadoria; Checagem apresenta alertas; Relatórios documenta; Auditoria reconstrói. Badges
`pending_review` ou `demo_unverified` significam que algo ainda não foi validado — não que esteja
errado ou aprovado.

## Exemplo

Se uma pessoa fictícia usa tramadol e o teste adiciona sertralina, pode aparecer “risco
serotoninérgico a revisar”. Isso significa conferir a associação e a fonte com profissional; não
significa diagnóstico de síndrome serotoninérgica.

## Perguntas frequentes

**O sistema receita?** Não. **A IA sabe a resposta final?** Não. **Os dados são completos?** Não;
seeds servem para demonstração. **Posso cadastrar pessoa real?** Não neste ambiente.

## Glossário e links

- **Fonte:** documento que sustenta uma regra.
- **Fallback:** resposta local quando IA externa não é usada.
- **Hash:** impressão digital usada para detectar alteração.
- **Policy:** regra institucional/regulatória/recomendação claramente classificada.

Veja [visão do produto](../product/product-overview.md) e [limitações](../product/known-limitations.md).
