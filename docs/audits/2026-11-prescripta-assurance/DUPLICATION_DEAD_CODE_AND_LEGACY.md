# Duplicação, código morto e legado

Método: busca de referências em todo o repositório (Python, TS/TSX, scripts, docs), verificação
de imports dinâmicos (`importlib`/`__import__`: nenhum alcança estes módulos), histórico Git e
testes. Classificação conforme o prompt: `DEAD_CONFIRMED`, `TEST_ONLY`, `PUBLIC_API`,
`COMPATIBILITY`, `DYNAMICALLY_REFERENCED`, `INTENTIONAL_ALIAS`, `UNKNOWN`, `LIVE`.

A primeira tabela cobre os candidatos PRE-08 e a revisão manual (CP-E, antes de as ferramentas
rodarem). A seção "Derivanta Engine" registra o inventário da ferramenta, executada depois. Nenhuma das
duas é prova de ausência de código morto: análise textual não vê uso dinâmico nem consumidores
externos.

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

## Derivanta Engine (`inspect --maintainability`)

Baseline em `6508221`: 345 candidatos INFO (182 sem referência, 94 duplicação, 69 complexidade). Dos
182 sem referência, 142 eram falsos positivos (handlers registrados por decorador) e 40 de fato sem
referência textual; a ferramenta foi corrigida (ENG-01) e, no mesmo escopo em `14f9be1`, caiu de 170
para 28. "Sem referência textual" não é "código morto": a tabela abaixo classifica cada um.

Removido em `14f9be1` por confirmação dupla (Engine + busca do agente em `backend/`, `scripts/`,
testes e frontend): `backend/app/core/constants.py` (módulo órfão), `MASS_TO_MG` e `VOLUME_TO_ML` em
`domain/dose.py`, `require_roles` em `core/auth.py`; os dois conjuntos inline de base por peso viraram
`WEIGHT_BASED_DOSE_BASES` (duplicação). Suíte verde depois da remoção (363 passed / 5 skipped).

Os 28 restantes não foram removidos nesta rodada. Cada nome foi buscado individualmente com
`git grep -w` no repositório inteiro (código, frontend, scripts, docs): todos aparecem só na própria
definição, exceto os 7 ports, citados também em
`docs/interoperability/future-clinical-integration-roadmap.md`. Uso dinâmico por string não foi
procurado de forma exaustiva.

| Grupo | Itens | Classe | Decisão |
|---|---|---|---|
| Ports e adapters de integração | 7 `*SourcePort`, 5 `Fhir*Adapter`, `MockHospitalAdapter` | PUBLIC_API (arquitetura de integração documentada em AGENTS.md; sem consumidor ativo) | Mantidos; remover ou ligar exige decisão de produto sobre integração (AGENTS: sem integração real sem API oficial). |
| Modelo de tabela | `CovariateDefinitionModel` | LIVE (registrado no metadata do SQLAlchemy/Alembic) | Mantido: remover a classe mudaria o schema. |
| Schemas Pydantic sem rota | `AICompletionRequest`, `AICompletionResult`, `PatientClinicalTimelineEventRead`, `ProtocolRunEventExport`, `TimelineEventRead` | UNKNOWN (podem ser contrato documentado) | Candidatos; checar OpenAPI e docs antes de remover. |
| Constantes e utilitários | `NotFoundError`, `CLINICAL_POLICY_VERSION`, `ALL_ROLES`, `REPORT_FOOTER`, `SUPPORTED_AI_PROVIDERS`, `ENTRY_BY_CATEGORY`, `is_supported_code`, `criterion_counts`, `PrescriptionRepository` | UNKNOWN | Candidatos para a próxima rodada de limpeza, um a um, com teste. |

## Não alterado (PRE-07)

Arquivos grandes (`database/models.py`, `database/seed.py`, `emergency_protocol_service.py`,
`frontend/src/services/api.ts`) não foram fatiados nesta rodada. Tamanho não é defeito por si; um
desmembramento sem ferramenta de grafo de chamadas e sem caracterização dirigida teria mais risco
(registro de modelos no Alembic, imports circulares, tipagem do cliente) do que benefício
demonstrado. Estado: DEFERRED.
