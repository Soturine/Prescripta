# Farmácia clínica

## Objetivo e acesso

Organizar intervenções farmacêuticas vinculadas ao paciente. Leitura, edição e decisão usam `pharmacy.intervention.read`, `.write` e `.decide`; a rota aceita quem tenha ao menos uma dessas capacidades, mas cada ação é revalidada.

## Seções e passos

1. Abra a fila e filtre por prioridade ou status.
2. Confira paciente, medicamento, tipo, recomendação, fontes e linha do tempo.
3. Registre uma proposta sustentada pela análise clínica.
4. Se autorizado, aceite ou rejeite explicitamente, com justificativa quando solicitada.
5. Confirme o novo status antes de sair.

## Exemplo e erros comuns

Uma intervenção pendente pode recomendar revisão de dose, mas permanece proposta até decisão humana. Escopo de paciente negado, transição inválida e conflito de atualização não devem ser contornados repetindo a ação em outra conta.

## Dados, auditoria, IA e autoridade

Intervenções, fontes, status e decisões são persistidos; criação, edição e decisão deixam trilha auditável. A IA pode redigir ou resumir uma proposta com fonte, nunca aceitá-la. A decisão humana autorizada e o motor determinístico são autoritativos.

## Limitações

A fila não substitui comunicação assistencial urgente. Ausência de intervenção registrada não comprova ausência de risco.
