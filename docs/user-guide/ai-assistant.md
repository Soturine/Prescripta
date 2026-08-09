# Assistente de IA

## Objetivo e acesso

Explicar alertas, resumir fontes recuperadas e propor texto em tarefas explicitamente suportadas. Ver status requer `ai.status.view`; apenas administradores podem salvar, apagar, testar ou ativar provedor e modelo.

## Uso seguro

1. Confirme a tarefa, as fontes e os dados que serão enviados.
2. Não inclua CPF, CNS, telefone, endereço, e-mail ou identificador real.
3. Leia referências, aviso de fallback e status de revisão.
4. Revise humanamente antes de aceitar ou publicar qualquer proposta.

## Exemplo e erros comuns

Uma explicação pode traduzir um alerta já calculado para linguagem clara. Ela não pode alterar severidade, dose, bloqueio ou recomendação. Fonte inexistente, campo reservado, JSON inválido ou falha do provedor fazem a resposta falhar de modo seguro ou usar fallback explícito.

## Dados, auditoria e autoridade

Configuração, provider/modelo, fallback e ações relevantes são auditados sem gravar chave. A chave nunca vai para `localStorage`. Regras determinísticas, fontes validadas e decisão humana são autoritativas.

## Limitações

A IA pode errar ou omitir contexto. Indisponibilidade externa não interrompe a decisão clínica determinística e não autoriza inferir conteúdo ausente.
