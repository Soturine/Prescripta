# Prescriber Policy Engine

## Quatro camadas que não devem ser confundidas

1. **Permissão do sistema:** role autorizado pelo backend a iniciar uma checagem/prescrição.
2. **Legal/regulatória:** somente com fonte oficial clara, jurisdição e versão.
3. **Política institucional:** regra local ou demonstrativa, sem alegação de lei geral.
4. **Recomendação clínica:** cautela ou revisão por especialidade, sem bloqueio legal.

O resultado informa status, perfil, regras aplicadas, especialidades obrigatórias/recomendadas,
credenciais ausentes, tipo de receita, avisos, notas e fontes. Auditor e enfermagem não prescrevem
por autorização do sistema. Médico sem perfil clínico recebe `insufficient_credentials`. Credencial
demo permanece `demo_unverified`; não há consulta a CRM/CFM/RQE.

Metadona e anestésicos usam políticas institucionais demo com revisão especializada e
monitoramento. Isso não significa que uma especialidade seja legalmente a única autorizada. Uma
regra marcada `legal_regulatory` sem fonte é rebaixada para aviso pendente de revisão.

## Escala e revisão

Os campos ficam no cadastro do medicamento, o que permite importação em lote e curadoria sem
condicionais por nome na interface. Bloqueios não regulatórios são apresentados como revisão
humana. Mudanças devem registrar autor, fonte, justificativa e evento de auditoria.
