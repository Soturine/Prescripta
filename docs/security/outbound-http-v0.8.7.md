# Saída HTTP e SSRF na v0.8.7

## Estratégia

O Prescripta usa um cliente de saída próprio para providers de IA. Cada requisição
resolve o hostname uma vez, valida todos os endereços retornados e conecta diretamente
a um desses endereços. O hostname original continua sendo usado no cabeçalho `Host`,
no SNI e na validação do certificado TLS. O cliente HTTP não faz uma segunda resolução.

Essa fixação elimina a janela de TOCTOU entre a validação DNS e a conexão dentro da
aplicação. O deployment ainda deve aplicar firewall ou proxy de egress como defesa em
profundidade; o projeto não afirma controlar a rede externa ao processo.

## Política por provider

- OpenAI usa somente `api.openai.com:443`.
- Gemini usa somente `generativelanguage.googleapis.com:443`.
- `openai_compatible` exige HTTPS, porta 443 e host exato em
  `PRESCRIPTA_AI_ALLOWED_HOSTS`.
- Ollama é aceito somente em ambiente local/teste, em loopback e porta 11434.
- Providers oficiais rejeitam Base URL customizada.

## Controles do cliente

- rejeição de userinfo, query e fragment em Base URLs;
- normalização IDNA, caixa e ponto final do hostname;
- rejeição de IPv4 alternativo, IPv6 mapeado e faixas não globais;
- allowlist e porta exatas;
- redirects bloqueados, sem reenvio de credencial;
- credenciais limitadas ao hostname esperado;
- TLS validado pelo trust store do runtime;
- timeout máximo de 30 segundos;
- request máximo de 1 MiB e resposta máxima de 2 MiB;
- retries limitados pelo serviço de IA e circuit breaker compartilhado;
- auditoria registra provider, hostname e finalidade, sem URL com query ou segredo.

Os testes adversariais cobrem loopback, metadata, link-local, encodings alternativos,
IPv6 mapeado, falha e alternância de DNS, redirects, porta, fragment, hostname enganoso,
tamanho, timeout e escopo de credenciais.
