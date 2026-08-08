# Modelo de fontes e vínculos

## EvidenceSource

Uma fonte registra tipo, título, identificador, URL opcional, jurisdição, versão, data de publicação,
licença, proveniência, metadados e estado de revisão. No contexto brasileiro, Bulário/Anvisa/DCB
devem ser priorizados; fontes internacionais precisam manter sua jurisdição explícita.

O registro guarda referência e metadados, não uma cópia integral de conteúdo protegido. A criação é
auditada e inicia em `pending_review`.

## EvidenceLink

O vínculo contém `source_id`, `target_type`, `target_id`, finalidade, locator opcional e estado de
revisão. O serviço confirma que a fonte pertence à mesma instituição antes de persistir. A unicidade
impede o mesmo vínculo lógico de ser criado mais de uma vez.

## Integridade e limites

- autorização real permanece no backend;
- um ID de fonte fora do tenant é rejeitado;
- a IA só pode citar IDs enviados e autorizados na tarefa;
- vínculo e revisão não substituem validação científica ou clínica;
- assinatura externa, timestamp confiável e armazenamento WORM não existem nesta versão.
