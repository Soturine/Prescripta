# Crosswalk de identificadores de achados

Duas fontes usam IDs `PRE-*` com significados parcialmente diferentes. Este arquivo evita dupla
contagem e mapeia cada achado para a fonte canônica, [FINDINGS_REGISTER.md](FINDINGS_REGISTER.md).
Nenhum documento histórico foi reescrito.

- **Fonte O (original):** `Prescripta_Auditoria_Tecnica_2026-11-04.md` (auditor anterior, revisão
  estática sobre `83d4bec`, sem execução).
- **Fonte E (execução):** este registro, iniciado em 2026-11-08 sobre o mesmo SHA, com reprodução.

| ID O | Tema | ID E | Estado E | SHA da correção | Evidência / teste | Remapeamento / reclassificação |
|---|---|---|---|---|---|---|
| PRE-01 | agregação de risco por idade | PRE-01 | VERIFIED (local + CI); política pendente de revisão clínica (ADR 010) | `a3e0469` | `test_age_risk_composition.py` (3 falham sem o fix); tabela de 18 cenários | Ampliado: também havia não monotonicidade dentro do `RiskEngine`. |
| PRE-02 | apresentação ambígua no CDS | PRE-02 | VERIFIED | `7b19394` | `test_cds_contract_hardening.py` | direto |
| PRE-03 | observações CDS ignoradas | PRE-03 | VERIFIED (declaradas `not_evaluated`, não interpretadas) | `7b19394` | idem | direto |
| PRE-04 | corrida de idempotência | PRE-04 | VERIFIED (injeção de corrida SQLite+PG); concorrência multi-conexão real: ver registro | `7b19394` | idem | Ampliado: auditoria era confirmada antes do insert (`auto_commit`). |
| PRE-05 | JWT sobrevive ao logout | PRE-05 | VERIFIED | `5144d4e` (série) | `test_session_revocation.py` | direto |
| PRE-06 | `JSON.contains` entre dialetos | PRE-06 | VERIFIED (SQLite+PG, CI postgres) | `3fab43f` | `test_object_scope_json_membership.py` | **Reclassificado média → alta**: em PostgreSQL `GET /api/patients` retornava 500. |
| PRE-07 | arquivos grandes | PRE-07 | DEFERRED | — | — | direto |
| PRE-08 | docs CDS × capacidades | **PRE-09** | VERIFIED | `7b19394` | `test_cds_docs_matrix.py` | ID deslocado na fonte E. |
| PRE-09 | pip-audit 24 registros | **PRE-10a** | VERIFIED (CI Security verde em `54614c0`) | `5a5a1ca` | pip-audit 0 | ID deslocado. |
| PRE-10 | Gitleaks `idempotency_key` | **PRE-10b** | FALSE_POSITIVE (VERIFIED) | `b35bdf5` | Gitleaks 8.24.3 histórico: 3 → 0 | ID deslocado. |
| PRE-11 | exceção CVE-2026-14456 expirada | **PRE-10c** | VERIFIED (exceção removida, não renovada) | `55c4e48` | Trivy local e CI Container verde | ID deslocado. |
| PRE-12 | candidatos a código morto | **PRE-08** | FIXED (2 removidos, 1 mantido LIVE, 1 frontend removido) | `2cfda4e` | [DUPLICATION_DEAD_CODE_AND_LEGACY.md](DUPLICATION_DEAD_CODE_AND_LEGACY.md) | ID deslocado. |
| — | release/docs e gates do RC | PRE-11 (E) | IN_PROGRESS | — | — | Complementar; não equivale ao PRE-11 da fonte O. |
| — | hipóteses diversas do prompt | PRE-12 (E) | parcial | vários | — | Complementar; não equivale ao PRE-12 da fonte O. |
| — | achados novos | NEW-01… | ver registro | vários | — | Não existiam na fonte O. |

Contagem sem duplicidade: 12 achados da fonte O mapeiam para 12 entradas distintas da fonte E; os
`NEW-*` e os PRE-11/PRE-12 de E são adicionais.
