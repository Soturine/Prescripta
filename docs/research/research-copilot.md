# Research Copilot v1

Tarefas disponíveis: estruturação da pergunta, revisão de completude do protocolo, rascunho de
coorte, rascunho do plano, explicação de Data Quality, explicação de resultados e resumo de jornada.

Toda saída é JSON estruturado com status de proposta e revisão pendente. Aceitar uma proposta cria
um novo draft quando existe contrato de domínio aplicável; o draft nunca nasce revisado. Resultados
numéricos e eventos citados precisam existir no contexto fornecido. Dados sensíveis usam somente
provider local permitido; a jornada sintética pode usar fallback após comprovação fail-closed.

Não há NL→SQL, execução de coorte/análise pela IA, decisão metodológica, cálculo estatístico, acesso
direto ao banco ou promoção automática de status.
