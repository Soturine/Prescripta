# Segurança e LGPD em integrações

Uma integração real exige contrato, base legal, finalidade, minimização, controle de acesso,
criptografia, retenção, rastreabilidade, resposta a incidente e avaliação do operador/controlador.
Tokens e credenciais nunca entram no payload clínico ou auditoria. A demo usa apenas dados
fictícios e não automatiza login em portais.

Antes de ativar um adapter: revisar ameaça, limitar tamanho/tipo, validar assinatura/autorização,
testar replay, definir idempotência, configurar observabilidade sem conteúdo sensível e obter
aprovação institucional.
