# Fontes Brasileiras de Medicamentos

Prescripta v0.5.0 prioriza Brasil/Anvisa/DCB para contexto brasileiro.

## Referencias oficiais

- Bulário Eletrônico da Anvisa: https://www.gov.br/anvisa/pt-br/sistemas/bulario-eletronico
- Página de DCB da Anvisa: https://www.gov.br/anvisa/pt-br/assuntos/farmacopeia/dcb
- Bulas, rótulos e nome comercial: https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/bulas-e-rotulos

O Bulário Eletrônico existe para acesso a bulas por populacao e profissionais de saude. A DCB e a nomenclatura brasileira oficial de principios ativos aprovada no ambito da vigilancia sanitaria.

## Regras do Prescripta

- Para `jurisdiction = BR`, a ordem de preferencia e Anvisa/Bulario, DCB e curadoria manual revisada.
- openFDA, DailyMed, FDA e RxNorm nao sao fonte primaria para decisoes no Brasil.
- Fontes internacionais podem ser usadas como referencia futura ou apoio secundario, sempre com jurisdicao explicita.
- O sistema nao promete cobertura completa de todos os medicamentos.
- A v0.5.0 nao faz scraping agressivo e nao assume API publica oficial onde ela nao estiver documentada.
- Todo dado demonstrativo deve manter `validation_status = demo` ou `pending_review`.

## Exemplo regulatorio

Dipirona/metamizol pode ter tratamento regulatorio diferente entre Brasil e Estados Unidos. No contexto BR, o Prescripta apresenta isso como diferenca regulatoria e prioriza fonte brasileira em vez de gerar erro automatico por fonte estrangeira.
