# Provenance de interações de IA

`AIInteraction` é o registro auditável de uma geração. Ele contém provider/modelo efetivo, template,
schema, tarefa, classificação, fontes, estudo/paciente quando aplicável, usuário, instituição,
latência, fallback, erro sanitizado e estado de revisão humana.

O input minimizado e a saída validada recebem hashes canônicos separados. O registro não guarda a
API key, o prompt bruto, PII de contato ou stack trace. `usage_metadata` declara que prompt bruto não
foi persistido e registra somente metadados disponíveis.

A revisão exige capacidade própria e ocorre uma única vez. Nota de revisão é representada por hash;
o estado passa de `needs_review` para `accepted` ou `rejected`. Aceitar uma interação não publica nem
executa o draft. A aplicação que desejar aproveitar a proposta precisa submetê-la ao workflow humano
e aos validadores determinísticos do domínio correspondente.

Hashes fornecem integridade de conteúdo, não não repúdio. Retenção institucional, DLP, contratos com
providers e avaliação formal de groundedness continuam controles externos.
