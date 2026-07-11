# Modo Sem Histórico

O modo sem histórico deixa claro quando a analise esta limitada por dados ausentes.

Mensagem base:

```text
Historico clinico incompleto. A analise sera baseada em medicamento, dose, duracao, efeitos principais e dados minimos disponiveis.
```

Dados faltantes listados:

- alergias;
- medicamentos continuos;
- condicao renal;
- condicao hepatica;
- gestacao/lactacao;
- perfil funcional;
- atividades que exigem atencao.

## Regras

- Falta de histórico não bloqueia automaticamente.
- O backend retorna `does_not_block_flow = true`.
- O risco personalizado fica explicitamente limitado.
- A UI mostra card `Dados faltantes` na checagem.
