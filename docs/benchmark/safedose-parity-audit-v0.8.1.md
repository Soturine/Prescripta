# Auditoria SafeDose/RicoToro v0.8.1

Este documento registra paridade conceitual sem copiar código, regra proprietária
ou interface de terceiros.

## Evolução Desde v0.8.0

- Relatórios e exportações já cobriam evidência, hash e auditoria.
- v0.8.1 adiciona prontidão de produto: health, scripts locais, UX de relatórios,
  IA hardening e reconciliação mais robusta.
- Deduplicação de medicamentos reconhece nomes comerciais brasileiros comuns para
  dipirona/metamizol.
- Identificadores externos são tratados com hash/máscara quando aceitos.

## Paridade Conceitual

| Capacidade | Prescripta v0.8.1 |
| --- | --- |
| Checagem determinística | Implementada no backend |
| Evidência rastreável | `ReportEvidenceBundle`, fontes e hash |
| Relatório técnico | PDF/preview/JSON/CSV |
| Auditoria filtrável | Eventos, filtros em URL, exportação e detalhe |
| IA assistiva | Explica/extrai, sem decisão |
| Fallback | Local, determinístico |
| Importação clínica | FHIR/JSON/CSV demonstrativo com revisão humana |

## Lacunas Mantidas

- Não há integração hospitalar real.
- Não há protocolo de emergência validado.
- Não há validação clínica externa formal.
- Não há migração PostgreSQL/Docker final nesta versão.

## Conclusão

v0.8.1 melhora a apresentação e a confiabilidade operacional, mas preserva o
limite central: Prescripta é educacional e não substitui avaliação profissional.
