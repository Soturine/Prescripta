# Pacientes

## Objetivo e acesso

Localizar pacientes, revisar contexto clínico e manter dados autorizados. A lista e o detalhe exigem `patient.read`; criar ou editar depende de capacidades adicionais e do escopo profissional.

## Pré-requisitos e seções

Use um ambiente aprovado e confirme a identidade antes de alterar dados. A lista oferece busca e estado de cadastro; o detalhe reúne resumo, medicamentos, alergias, condições, exames, perfil funcional e histórico disponível.

## Passos

1. Acesse **Pacientes** e pesquise pelo identificador permitido no ambiente.
2. Abra o registro correto e confira o contexto antes de qualquer ação.
3. Atualize somente campos sustentados por fonte clínica válida.
4. Salve e confirme a mensagem de sucesso ou corrija os campos indicados.

## Exemplo e erros comuns

Em demonstração, selecione um paciente sintético e confira alergias antes da checagem. Registro inexistente, duplicidade, escopo negado e campos inválidos têm tratamentos diferentes; não recrie um paciente apenas porque uma busca falhou.

## Dados, auditoria, IA e autoridade

Cadastros e alterações são persistidos no banco e geram eventos de auditoria com ator e recurso. A IA não cria identidade nem substitui dados clínicos. O registro confirmado e suas fontes humanas são autoritativos.

## Limitações

Dados incompletos reduzem a confiança das análises. Nunca use dados sensíveis reais em seeds, testes ou exemplos.
