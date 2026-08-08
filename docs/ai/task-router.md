# AI Task Router / Provider Gateway

`AITaskRouter` recebe uma tarefa tipada, aplica policy de provider e classificação de dados, minimiza
o contexto, chama o provider configurado ou fallback e valida a saída antes de persistir uma
`AIInteraction`.

## Tarefas registradas

- explicação de decisão clínica;
- estruturação de pergunta de pesquisa;
- draft de coorte e de protocolo;
- resumo de evidência;
- resumo de jornada do paciente;
- explicação de Data Quality.

Cada tarefa tem template versionado. Providers conhecidos são `fallback`, `openai`, `gemini`,
`ollama` e `openai_compatible`. Dados `sensitive` ou `restricted` ficam limitados a provider local
autorizado (`ollama`) ou fallback; indisponibilidade local não faz fail-open para provider externo.

## Guardrails

- o payload inclui finalidade, classificação, limite de contexto e fontes autorizadas;
- estudo, paciente e fontes são verificados no escopo institucional;
- prompts brutos não são persistidos;
- draft de coorte precisa passar pelo mesmo validador da DSL;
- claims de evidência só aceitam `source_id` enviado na requisição;
- o LLM não executa coorte, não conta pacientes e não escreve em tabelas clínicas ou de pesquisa;
- falha externa usa fallback determinístico apenas quando a policy permitir.

Toda saída permanece `needs_review`. Aceite ou rejeição humana é outra operação, auditada e sem
efeito automático sobre decisões, protocolos, coortes ou dados do paciente.
