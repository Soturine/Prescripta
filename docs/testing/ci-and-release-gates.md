# CI e gates de release

O CI executa qualidade do repositório, backend em Ubuntu e Windows, frontend, PostgreSQL/Alembic,
smoke controlado e um job final `release-readiness`. O backend mede statements e branches de `app`,
com gate mínimo de 80%; a linha v0.8.6 mede 81,28%. Conversões dimensionais também possuem teste
baseado em propriedades com Hypothesis. O smoke só inicia quando os grupos anteriores passam.

O checker textual é Python puro. Links e assets possuem verificadores separados, e whitespace é
validado no commit com `git show --check`, adequado a um checkout limpo.

Para publicar, execute `scripts/release-preflight.ps1` ou `.sh` na `main` limpa. O script valida a
versão, executa os gates locais, envia o commit e espera o GitHub Actions referente ao mesmo SHA.
Falha ou timeout não autoriza tag. Smoke não é denominado E2E; cenários Playwright executam
login por perfil, paciente, catálogo, checagem, protocolo, relatórios, auditoria, fallback e mobile.

O workflow `security.yml` adiciona CodeQL, `pip-audit`, audit npm com risco aceito e prazo explícito,
gitleaks e SBOM CycloneDX. Actions são fixadas por SHA. Esses gates não substituem pentest, análise de
licenças por advogado, validação clínica ou revisão independente de uma implantação.
