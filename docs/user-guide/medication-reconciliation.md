# Reconciliação medicamentosa

## Objetivo e acesso

Revisar itens importados sem sobrescrever silenciosamente o prontuário. A rota **Importações clínicas** requer `reconciliation.review` e um lote disponível.

## Seções e passos

1. Abra o lote e confirme origem, paciente e consentimento aplicável.
2. Compare cada item importado com o dado atual.
3. Aceite ou rejeite cada item individualmente e registre a justificativa.
4. Revise o resumo antes de concluir.
5. Confirme no histórico quais itens foram aplicados.

## Exemplo e erros comuns

Um nome de medicamento semelhante não deve ser aceito sem confirmar substância, forma e contexto. Fonte ausente, paciente divergente, lote já processado e integração indisponível exigem investigação.

## Dados, auditoria, IA e autoridade

O conteúdo original é preservado; decisões granulares e alterações aceitas são persistidas e auditadas. A IA não decide correspondência nem altera o importado. A escolha humana autorizada sobre o item e o registro resultante são autoritativos.

## Limitações

O ambiente demonstrativo não representa integração hospitalar real. Produção requer API oficial, contrato, segurança e conformidade com a LGPD.
