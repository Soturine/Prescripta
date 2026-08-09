# Qualidade dos dados

`DataQualityRun` persiste horário, executor, escopo opcional do estudo, resumo por regra/severidade,
dimensões e hash de conteúdo. Findings não contêm PII e são deduplicados pelo fingerprint lógico de
instituição, regra, recurso, identificador e campo.

As dimensões demonstrativas são completude, validade, consistência e conformidade. Checks cobrem
datas impossíveis, fim antes do início, quantidade não positiva, unidade desconhecida, conceito órfão,
exposição medicamentosa inconsistente e critério sem concept set válido.

Finding crítico aberto bloqueia execução da análise; severidades menores permanecem visíveis e não
são silenciosamente reduzidas. Acknowledgement exige capacidade própria, justificativa humana,
ator/horário e auditoria. A IA pode explicar o finding, mas não reconhecer, resolver nem alterar
severidade.
