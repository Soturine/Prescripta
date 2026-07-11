# Guia para auditores

Eventos cobrem autenticação, checagem, explicação, relatório/exportação, protocolos, importações,
curadoria, perfil clínico do usuário e avaliação de dose/política/sinais. `GeneratedReport` registra
tipo, alvo, versão, hash do EvidenceBundle, provider/modelo, prompt, IA/fallback e anonimização.

A trilha permite reconstruir entrada, regras disparadas, fontes e decisão humana. Filtros clínicos
incluem especialidade, tipo/força de política, regra de dose, código psicotrópico, status do
prescritor, verificação de credencial e categoria de alto risco. Uma política institucional fora da
especialidade recomendada deve aparecer como revisão, não como suposta infração legal.

Na revisão, compare o hash, confirme que `source_id` existe, verifique versão/jurisdição/status e
procure campos reservados indevidos na narrativa. API key e dados identificáveis não podem constar
em relatório ou log. Fallback é comportamento esperado e deve permanecer visível.

## Passo a passo

Filtre no servidor por período/recurso; abra evento; confira timeline e evidências; compare target e
hash; verifique provider/modelo/fallback; procure override ou segunda revisão; exporte somente no
modo autorizado. A página é aplicada no SQL, não depois de carregar todos os eventos.

## Exemplo e interpretação

Uma checagem fora da especialidade recomendada deve registrar `requires_specialist_review` com
`demo_policy`; isso não é violação legal. Uma regra `legal_regulatory` sem fonte é inconsistência.

## FAQ, glossário e links

**Hash prova correção clínica?** Não, prova integridade do bundle. **Fallback é falha?** Nem sempre;
é modo esperado. Veja [relatório de auditoria](../audits/v0.8.5-full-repository-audit.md) e
[EvidenceBundle](../reports/report-evidence-bundle.md).
