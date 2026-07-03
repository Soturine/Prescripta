# Caso De Uso: Histórico Do Paciente

Uma pessoa da área da saúde apontou que dose diária isolada não basta. A v0.4.0 responde a essa ideia com um fluxo que cruza medicamento pretendido, histórico clínico e duração.

## Fluxo

1. O profissional abre o paciente.
2. Revisa o perfil clínico inteligente.
3. Preenche a triagem rápida.
4. Informa dose, frequência, duração e indicação na checagem.
5. O motor determinístico calcula alertas, dose acumulada e compatibilidade.
6. O RAG interno recupera trechos demonstrativos.
7. A IA explica o contexto sem alterar o resultado.
8. Alternativas cadastradas são avaliadas pelo motor de risco antes de aparecerem.

## Valor

O Prescripta passa a apoiar uma revisão mais contextual: paciente, medicamento, dose, duração, histórico e evidência interna demonstrativa.
