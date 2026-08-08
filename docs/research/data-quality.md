# Data Quality para Research/RWE

`DataQualityService` executa checks determinísticos por instituição e persiste metadados de achados,
sem copiar PII para a descrição. A execução e sua contagem são auditadas.

## Regras iniciais

- data futura impossível;
- fim anterior ao início;
- dose ou quantidade não positiva;
- unidade desconhecida pelo contrato dimensional;
- código clínico sem sistema terminológico;
- término de medicamento anterior ou sem início rastreável;
- critério de coorte clínico sem versão institucional válida de concept set.

Cada achado informa regra, severidade, recurso, campo, mensagem, fonte, estado e horário. A chave
lógica impede duplicar o mesmo achado aberto em execuções repetidas.

Data Quality não corrige o dado, não aprova estudo e não transforma resultado em evidência válida.
IA pode explicar um conjunto já calculado, mas não altera severidade, estado ou contagem. Regras de
completude, plausibilidade e consistência adicionais fazem parte do roadmap do MVP v0.9.0.
