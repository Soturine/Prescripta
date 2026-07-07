# IA Explicativa

A IA explicativa do Prescripta ajuda a transformar alertas já calculados pelo backend em texto claro para revisão profissional.

Ela não decide risco, não libera prescrição, não calcula dose crítica e não substitui revisão humana.

## v0.7.1

A configuração ativa vem de `AISettingsService`, que lê:

- provider;
- modelo;
- chave protegida;
- Base URL;
- chamadas externas habilitadas/desabilitadas;
- modo JSON.

O endpoint `POST /api/prescriptions/explain` usa essa configuração. Se provider externo estiver indisponível, desabilitado, sem chave ou sem modelo válido, a resposta usa fallback determinístico.

## Entrada

A IA recebe somente o resultado já calculado:

- paciente e medicamento;
- dose, frequência, via e duração;
- status e risco determinísticos;
- alertas;
- compatibilidade;
- evidências RAG;
- alternativas já avaliadas pelo motor de risco;
- orientações ao paciente, quando disponíveis.

## Saída

A resposta contém:

- explicação simples;
- resumo técnico;
- perguntas de revisão;
- aviso educacional;
- status e risco originais;
- códigos críticos preservados;
- fontes RAG citadas;
- seção `Como explicar ao paciente`, quando houver `patient_counseling`.

## Salvaguardas

- JSON estruturado é validado.
- Fallback local é sempre disponível.
- API Key nunca aparece em payload, log ou auditoria.
- Fontes internacionais são apoio secundário no contexto brasileiro.
- A IA não altera decisão determinística.

## Documentos Relacionados

- [Configuração de provider](provider-configuration.md)
- [Seleção e atualização de modelos](model-selection-and-refresh.md)
- [Tratamento seguro de API Key](secure-api-key-handling.md)
- [Counseling extractor](counseling-extractor.md)
