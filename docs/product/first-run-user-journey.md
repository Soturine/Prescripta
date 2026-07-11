# Jornada Inicial de Uso

## Objetivo

Este roteiro ajuda uma pessoa que acabou de clonar o projeto a validar o produto
em poucos minutos, sem depender de dados reais nem de provider externo de IA.

## Roteiro

1. Rode `scripts/setup-dev.ps1`.
2. Rode `scripts/check-install.ps1`.
3. Rode `scripts/dev.ps1`.
4. Abra `http://127.0.0.1:5173`.
5. Entre como `admin@prescripta.local` com senha `Admin@12345`.
6. Confira o Dashboard e a versão `v0.8.2`.
7. Em Medicamentos, busque `Novalgina` e veja resolução para dipirona.
8. Em Checagem, simule uma prescrição com paciente e medicamento demo.
9. Gere explicação e orientação ao paciente.
10. Em Importações, use o exemplo JSON/FHIR e revise itens.
11. Em Relatórios, abra preview, PDF, JSON e timeline.
12. Em Protocolos, execute Hipoglicemia ou Anafilaxia com contexto artificial.
13. Em Auditoria, filtre por `protocol.run` ou por prescrição.
14. Em IA, veja provider, fallback, cache e circuit breaker.

## Resultado Esperado

Ao final, o usuário entende que o Prescripta é um sistema integrado: regras
determinísticas, IA limitada, reconciliação, relatórios, protocolos e auditoria
conversam entre si.

## Limites

Não usar dados sensíveis reais. O fluxo é demonstrativo e educacional.
