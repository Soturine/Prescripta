# Counseling Extractor

`MedicationCounselingExtractor` transforma trechos recuperados em JSON estruturado.

## Fluxo

1. Resolver medicamento/princ?pio ativo.
2. Recuperar texto de RAG, fonte cadastrada ou trecho informado.
3. Enviar ao provider apenas o texto recuperado.
4. Validar JSON com Pydantic.
5. Normalizar categorias pela taxonomia controlada.
6. Salvar como `pending_review`.
7. Exigir revis?o humana para `curated` ou `validated`.

## Providers

- `GPTProvider`: OpenAI-compatible quando provider e chave/base estiverem configurados.
- `GeminiProvider`: demonstrativo com fallback nesta versao.
- `LlamaProvider`: OpenAI-compatible para endpoint local/gateway confiavel.
- `FallbackDeterministicProvider`: extrai termos apenas dos trechos recebidos.

## Prompt interno

O provider recebe instrucao para ler apenas os trechos fornecidos, n?o usar conhecimento externo, n?o inventar efeitos, marcar evidencia insuficiente e citar `source_id`/trecho quando possivel.

## Salvaguardas

- JSON invalido e rejeitado.
- Categorias desconhecidas sao descartadas.
- `confidence = insufficient_evidence` quando o texto n?o sustenta resumo.
- O extrator n?o escreve status da prescri??o.
- A IA n?o reduz severidade, n?o libera bloqueio e n?o substitui revis?o profissional.
