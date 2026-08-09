# CI e gates de release

O CI executa qualidade do repositório, backend em Ubuntu e Windows, frontend Linux, regressão visual
Chromium em Windows, PostgreSQL/Alembic, smoke controlado e um job final `release-readiness`. O backend
mede cobertura combinada e branches de `app` separadamente, com ratchets de 82% e 65%. Conversões
dimensionais também possuem teste baseado em propriedades com Hypothesis. O smoke só inicia quando
todos os grupos anteriores, inclusive visual e PostgreSQL, passam.

Vitest mede o frontend com gates de 81% statements, 69% branches, 75% functions e 84% lines. As únicas
exclusões são tipos, bootstrap trivial, testes, configuração e tokens puramente declarativos.
Playwright recria banco/seed por execução e cobre perfis, BOLA, dose, override, axe, falha/retry/vazio,
Research/RWE aggregate-first, attrition, pharmacy, desktop/mobile/tablet e reduced motion. Snapshots
Windows não são comparados a rasterização Linux.

O checker textual é Python puro. Links e assets possuem verificadores separados, e whitespace é
validado no commit com `git show --check`, adequado a um checkout limpo.

Para publicar, execute `scripts/release-preflight.ps1` ou `.sh` na `main` limpa. O script valida a
versão, executa os gates locais, envia o commit e espera o GitHub Actions referente ao mesmo SHA.
Falha ou timeout não autoriza tag. Smoke não é denominado E2E; cenários Playwright executam
login/logout/sessão expirada, navegação por capacidade, paciente/grants, checagem, protocolos,
override/revisão, auditoria, falhas e responsividade.

O workflow `security.yml` adiciona CodeQL, `pip-audit`, audit npm sem exceção high/critical ativa,
gitleaks, inspeção de install scripts e SBOM CycloneDX. O workflow `container.yml` executa smoke,
Trivy HIGH/CRITICAL e SBOM das imagens. Actions são fixadas por SHA. Esses gates não substituem
pentest, análise de licenças por advogado, validação clínica/epidemiológica ou revisão independente
de uma implantação.
