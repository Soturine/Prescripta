# IA Explicativa

## Atualizacao v0.6.0

A IA pode explicar, quando o backend ja tiver calculado:

- dose diaria, dose acumulada, duracao e uso continuo;
- necessidade de monitoramento;
- mecanismo, metabolismo, eliminacao, CYP e perfil ADME;
- alertas neuropsiquiatricos;
- alertas reprodutivos/ginecologicos;
- dados importados pendentes de revisao;
- por que revisao humana e necessaria.

A IA continua proibida de liberar prescricao bloqueada, reduzir severidade, inventar fonte, generalizar antibioticos/anticoncepcionais ou transformar regra demonstrativa em decisao clinica definitiva.

## Atualizacao v0.5.0

Na v0.5.0, a IA continua apenas explicativa. A mudanca principal e que o payload agora pode incluir fonte, jurisdicao, tipo de evidencia, status de validacao, principio ativo e aliases comerciais vindos do RAG.

A IA pode explicar:

- se a evidencia e demonstrativa, manual, Anvisa/DCB ou externa;
- se a fonte tem `jurisdiction = BR`;
- quando uma fonte externa e apenas secundaria no contexto brasileiro;
- quando um dado esta `pending_review`;
- por que dipirona/metamizol pode ter diferenca regulatoria entre paises.

A IA nao pode:

- alterar status final;
- rebaixar risco critico;
- liberar prescricao bloqueada;
- decidir dose;
- usar fonte estrangeira como regra primaria brasileira sem aviso.

Prescripta v0.4.0 mantém a IA como camada explicativa responsável. Ela apoia a compreensão dos alertas gerados pelo motor determinístico e do contexto clínico demonstrativo, mas não decide a prescrição.

Esta camada não calcula risco, não libera prescrição, não recalcula dose crítica e não substitui revisão profissional. O backend continua sendo a fonte das regras clínicas demonstrativas.

## Escopo

A IA recebe o resultado já calculado pela checagem de prescrição e gera:

- explicação em linguagem simples;
- resumo técnico curto;
- perguntas de revisão clínica;
- dados do paciente considerados;
- dados ainda faltantes;
- referência às evidências internas demonstrativas;
- aviso educacional obrigatório.

Contexto usado:

- alertas determinísticos;
- dose diária, frequência, duração e dose acumulada;
- compatibilidade paciente-medicação;
- perfil clínico estruturado;
- efeitos adversos e cautelas por órgão/sistema;
- Clinical Context Graph;
- evidências RAG internas;
- alternativas já avaliadas pelo motor de risco.

## Endpoint

`POST /api/prescriptions/explain`

Permissão: `admin`, `medico` e `enfermagem`.

O endpoint recebe paciente, medicamento, dose, frequência, via, perfil do usuário e o resultado da checagem de prescrição. A resposta ecoa `prescription_status`, `risk_level` e `critical_alert_codes` para deixar explícito que a IA não alterou a decisão determinística.

## Configuração

Variáveis:

- `PRESCRIPTA_AI_PROVIDER`: `fallback` por padrão; aceita `openai`, `local`, `llama` e `gemini` como opções demonstrativas.
- `PRESCRIPTA_AI_API_KEY`: chave do provider, nunca versionada.
- `PRESCRIPTA_AI_MODEL`: modelo usado quando o provider externo estiver configurado.
- `PRESCRIPTA_AI_BASE_URL`: endpoint OpenAI-compatible para Llama/local ou outro gateway confiável.

Sem chave de API, o sistema retorna fallback determinístico baseado nos alertas, na compatibilidade e no RAG textual interno. A falha do provider externo também cai no fallback para não quebrar o fluxo de checagem.

Detalhes de provider: [multi-provider-ai.md](multi-provider-ai.md)

## Salvaguardas

- chamada somente por clique do usuário;
- sem chamada automática a cada prescrição;
- endpoint protegido por perfil;
- auditoria registra metadados da explicação, não o texto completo;
- prompt orienta o modelo a explicar, não decidir;
- resposta preserva códigos de alertas críticos;
- RAG interno é marcado como demonstrativo;
- alternativas são apresentadas como opções para avaliação profissional;
- testes verificam fallback, permissão, status inalterado e preservação de bloqueios críticos.

## Uso Responsável

O texto gerado é apoio educacional/demonstrativo. Ele deve ser revisado por profissional habilitado e confrontado com protocolos locais, histórico completo do paciente e julgamento clínico.
