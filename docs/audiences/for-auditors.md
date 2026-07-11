# Guia para auditores

Eventos cobrem autenticação, checagem, explicação, relatório/exportação, protocolos, importações,
curadoria, perfil clínico do usuário e avaliação de dose/política/sinais. `GeneratedReport` registra
tipo, alvo, versão, hash do EvidenceBundle, provider/modelo, prompt, IA/fallback e anonimização.

A trilha permite reconstruir entrada, regras disparadas, fontes e decisão humana. Filtros clínicos
incluem especialidade, tipo/força de política, regra de dose, código psicotrópico, status do
prescritor, verificação de credencial e categoria de alto risco. Uma política institucional fora da
especialidade recomendada deve aparecer como revisão, não como suposta infração legal.

Na revisão, compare o hash, confirme que `source_id` existe, verifique versão/jurisdição/status e
procure campos reservados indevidos na narrativa. API key e dados identificáveis não podem constar
em relatório ou log. Fallback é comportamento esperado e deve permanecer visível.
