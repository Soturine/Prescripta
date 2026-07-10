# Anonimização de Relatórios

O modo `anonymized` reduz identificadores diretos.

Exemplos:

- nome do paciente vira `Paciente #P-00042`;
- CPF deve ser omitido ou mascarado;
- CNS deve ser omitido ou mascarado;
- telefone, e-mail e endereço não entram no bundle externo;
- identificadores externos reais não são exportados no modo anonimizado.

Na v0.8.0, o envio de dados identificáveis para IA externa não é implementado.
Mesmo relatórios internos completos usam payload minimizado quando acionam IA.

O hash do `ReportEvidenceBundle` muda quando o modo de relatório muda, pois o
conteúdo do bundle também muda.
