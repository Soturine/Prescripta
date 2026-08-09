# Permissões e acesso

## Objetivo

Explicar por que usuários veem módulos e ações diferentes. O Prescripta combina papel, capacidade, organização, escopo de paciente e estado do recurso.

## Como verificar

1. Confirme usuário, organização e papel da sessão.
2. Consulte a ação desejada e a capacidade indicada no guia da rota.
3. Em **Acesso negado**, registre o contexto e solicite revisão administrativa.
4. Administradores devem conceder o menor conjunto necessário e revisar mudanças.

## Exemplos e erros comuns

`patient.read` libera leitura de pacientes, mas não autoriza editar ou ver todo paciente. `pharmacy.intervention.read` permite entrar na fila, enquanto decidir exige `.decide`. Ocultar botão no frontend não é controle suficiente.

## Dados, auditoria, IA e autoridade

Usuários, papéis e capacidades são persistidos; alterações e negações relevantes podem ser auditadas. A IA não concede acesso. A decisão do backend sobre a requisição atual é autoritativa.

## Limitações

Capacidades não substituem consentimento, vínculo assistencial, finalidade legítima ou política organizacional.
