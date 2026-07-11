# Tratamento de erros de integração

Payload inválido retorna 422 sem aplicar itens. Conflitos de identidade ou duplicação retornam 409
e exigem revisão humana. Falha de autenticação/autorização usa 401/403; recurso ausente usa 404.
Erros transitórios podem ser reenviados com a mesma chave de idempotência, nunca por loop infinito.

Cada lote registra origem, versão do contrato, hash, usuário, status e itens aceitos/rejeitados. Um
erro não autoriza sobrescrever silenciosamente dado importado nem apagar histórico local.

