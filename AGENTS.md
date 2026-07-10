# AGENTS.md

Guia para agentes e colaboradores que forem evoluir o Prescripta.

## Layout

- `backend/app/domain`: entidades, enums e objetos de resultado.
- `backend/app/services`: regras determinísticas, contexto clínico, alternativas e serviços de aplicação.
- `backend/app/services/ai_settings.py`: configuração central de IA, credenciais, modelos e chamadas externas.
- `backend/app/services/ai_explainer.py`: camada explicativa; não decide risco.
- `backend/app/services/medication_counseling_extractor.py`: extrator IA/RAG de resumo prático; usa apenas fonte recuperada.
- `backend/app/services/medication_counseling_service.py`: cache, geração e revisão humana de orientações ao paciente.
- `backend/app/services/patient_counseling_service.py`: orientações, modo sem histórico e pergunta contextual.
- `backend/app/services/patient_functional_profile.py`: perfil funcional do paciente.
- `backend/app/services/adverse_effect_taxonomy.py`: taxonomia controlada de efeitos adversos.
- `backend/app/reports`: motor de relatórios, EvidenceBundle, PDF simples, exportações JSON/CSV, narrativa controlada por IA e auditoria.
- `backend/app/reports/prompts`: prompts versionados de relatórios; não podem permitir decisão clínica pela IA.
- `backend/app/integrations`: ports, adapters, mapeamento, consentimento e auditoria de importações clínicas.
- `backend/app/integrations/services/clinical_reconciliation_service.py`: reconciliação granular por item.
- `backend/app/knowledge`: RAG educacional com busca textual e normalização.
- `backend/app/api/routes/settings.py`: endpoints de configuração de IA.
- `backend/tests`: testes unitários e de API.
- `frontend/src/pages`: telas de navegação.
- `frontend/src/pages/AISettings.tsx`: tela de configuração de IA.
- `frontend/src/components`: componentes reutilizáveis.
- `frontend/src/services`: cliente HTTP e integração com API.
- `scripts`: utilitários locais.
- `docs`: documentação de arquitetura, produto, regras clínicas, segurança e releases.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd frontend
npm install
```

## Testes

```powershell
cd backend
..\.venv\Scripts\python -m pytest
```

```powershell
cd frontend
npm run build
```

## Lint

```powershell
cd backend
..\.venv\Scripts\python -m ruff check . --no-cache
```

```powershell
cd frontend
npm run lint
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-text-quality.ps1
```

## Convenções

- Use TypeScript estrito no frontend.
- Use Pydantic para contratos de API e SQLAlchemy para persistência.
- Não misture regra de negócio com componentes React.
- Não implemente regra de risco diretamente em rota FastAPI; use `backend/app/services`.
- Não implemente regra decisória no frontend.
- Backend é a fonte real de autorização; frontend pode esconder menus, mas nunca substituir checagem de perfil.
- Não registre senha, API Key ou segredo em auditoria, log ou payload de resposta.
- API Key de IA nunca deve ser salva em `localStorage`.
- Apenas `admin` pode salvar, apagar, testar ou ativar provider/modelo de IA.
- Médicos, enfermagem e auditoria podem ver status de IA, mas nunca a chave.
- IA deve apenas explicar alertas, extrair/classificar com fonte e resumir conteúdo recuperado.
- IA em relatórios deve atuar apenas como compositora narrativa sobre `ReportEvidenceBundle`.
- Nunca permita que IA altere status, risco, bloqueio, dose crítica ou recomendação final.
- Nunca envie CPF, CNS, telefone, endereço, e-mail ou identificador real para IA externa em relatórios.
- Rejeite narrativa de relatório se a IA retornar campo reservado ou `source_id` inexistente.
- Relatórios e exportações devem registrar auditoria, hash do bundle, provider/modelo e fallback.
- Resumos práticos gerados por IA/fallback devem retornar JSON validado e permanecer `pending_review` até revisão humana.
- Perfil funcional e modo sem histórico orientam cautelas práticas, mas não bloqueiam prescrição automaticamente.
- Reconciliação clínica granular deve registrar aceite/rejeição por item e não alterar dado importado sem decisão humana.
- Preserve fallback determinístico quando não houver chave, chamadas externas estiverem desabilitadas ou provider externo falhar.
- RAG interno não decide risco, não substitui bula validada e deve permanecer marcado como educacional/pendente quando aplicável.
- Para contexto brasileiro, priorize Anvisa/Bulário/DCB e marque fonte, jurisdição e status de validação.
- Fontes internacionais são secundárias no contexto BR e devem ser explicitamente identificadas.
- Não implemente scraping agressivo de Anvisa, hospitais ou portais.
- Não implemente integração hospitalar real sem API oficial, contrato, segurança e LGPD.
- Alternativas terapêuticas devem vir da base cadastrada e passar pelo motor de risco antes de aparecerem.
- Triagem rápida não deve apagar histórico clínico existente sem auditoria.
- Atualize documentação quando alterar comportamento de produto, API, regra clínica, segurança ou configuração.
- Atualize `CHANGELOG.md` em mudanças relevantes.
- Não versionar `.env`, bancos locais, caches, `node_modules` ou `dist`.
- Não usar dados sensíveis reais em seeds, testes ou exemplos.

## Commits

Use Conventional Commits:

- `feat(backend): ...`
- `feat(frontend): ...`
- `test(backend): ...`
- `docs: ...`
- `ci: ...`
- `chore(release): ...`
