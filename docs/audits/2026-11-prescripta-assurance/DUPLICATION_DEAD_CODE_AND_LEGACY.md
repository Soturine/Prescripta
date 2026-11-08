# Duplicação, código morto e legado

Método: busca de referências em todo o repositório (Python, TS/TSX, scripts, docs), verificação
de imports dinâmicos (`importlib`/`__import__`: nenhum alcança estes módulos), histórico Git e
testes. Classificação conforme o prompt: `DEAD_CONFIRMED`, `TEST_ONLY`, `PUBLIC_API`,
`COMPATIBILITY`, `DYNAMICALLY_REFERENCED`, `INTENTIONAL_ALIAS`, `UNKNOWN`, `LIVE`.

Ferramentas de análise (Derivanta Engine `--maintainability`, Assertiva) **não foram executadas**:
a instalação foi negada pelo classificador de permissões do ambiente. Esta lista cobre os
candidatos PRE-08 e o que surgiu na revisão manual; não é um inventário exaustivo de código morto.

| Item | Referências encontradas | Classe | Decisão |
|---|---|---|---|
| `backend/app/services/dose_calculator.py::calculate_daily_dose` | só `tests/test_dose_calculator.py`; era um alias de uma linha para `PrescriptionInput.daily_total_mg`, que `check_max_daily_dose` já usa | TEST_ONLY | **Removido**; o teste passou a afirmar a propriedade diretamente. |
| `backend/app/knowledge/normalizer.py` | nenhum import em `backend/`, `scripts/` ou testes; citado só em `docs/audits/v0.8.6-…` (histórico) | DEAD_CONFIRMED | **Removido** (reexport de `services.normalizer`). |
| `backend/app/services/text.py` | importado por `allergy_checker.py` e `risk_engine.py` | LIVE / INTENTIONAL_ALIAS | Mantido: reexporta `normalize_text` e fornece `any_token_matches`. |
| `frontend/src/services/api.ts::setAuthToken` | só `api.test.ts`; o app usa sessão por cookie (`AuthContext` usa sentinela `cookie-session`) | TEST_ONLY | **Removido**: colocar Bearer em JS incentivaria guardar token fora do cookie HttpOnly. `clearAuthToken` permanece (LIVE: interceptor 401 e logout) e segue testado. |
| `RiskEngine` × `ClinicalDecisionOrchestrator` (composição de risco) | dois cálculos divergentes do nível agregado | duplicação semântica | **Unificado** em `compose_risk_level` (PRE-01). |
| quatro definições de "ambiente local" | `config`, `auth`, `session`, `ai_settings` | duplicação semântica | **Unificado** em `is_local_environment` (NEW-10). |
| `backend/app/database/session.py::_ensure_sqlite_v04_columns` | chamado por `init_db` em SQLite local | COMPATIBILITY | Mantido: atualiza bancos demo pré-Alembic; remover exige decisão de suporte a demos antigos. |
| `MedicationRepository.list()` com `limit=50` em varredura | `AlternativeService` | uso incorreto | **Corrigido** com `iter_all()` (NEW-04). |

## Não alterado (PRE-07)

Arquivos grandes (`database/models.py`, `database/seed.py`, `emergency_protocol_service.py`,
`frontend/src/services/api.ts`) não foram fatiados nesta rodada. Tamanho não é defeito por si; um
desmembramento sem ferramenta de grafo de chamadas e sem caracterização dirigida teria mais risco
(registro de modelos no Alembic, imports circulares, tipagem do cliente) do que benefício
demonstrado. Estado: DEFERRED.
