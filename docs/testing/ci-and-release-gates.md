# CI e gates de release

O CI executa qualidade do repositório, backend em Ubuntu e Windows, frontend, smoke controlado e
um job final `release-readiness`. O smoke só inicia quando os três grupos anteriores passam.

O checker textual é Python puro. Links e assets possuem verificadores separados, e whitespace é
validado no commit com `git show --check`, adequado a um checkout limpo.

Para publicar, execute `scripts/release-preflight.ps1` ou `.sh` na `main` limpa. O script valida a
versão, executa os gates locais, envia o commit e espera o GitHub Actions referente ao mesmo SHA.
Falha ou timeout não autoriza tag. Smoke não é denominado E2E; dez cenários Playwright executam
login por perfil, paciente, catálogo, checagem, protocolo, relatórios, auditoria, fallback e mobile.
