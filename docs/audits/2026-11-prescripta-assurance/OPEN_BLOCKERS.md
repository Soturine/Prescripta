# Bloqueios abertos

| # | Ação bloqueada | Quem bloqueou | Tentativas | O que destrava | Trabalho independente feito |
|---|---|---|---|---|---|
| 1 | Instalar Derivanta Engine e Assertiva em venv próprio (`python -m pip install -e .` no checkout de cada ferramenta) e executar `derivanta-engine inspect` / `assertiva audit [--execute]` | Classificador de permissões do Claude Code ("Code from External"; depois "Auto-Mode Bypass") | 2 (2026-11-08) | O usuário adicionar uma regra de permissão para esses comandos nos checkouts `../Derivanta-Engine` e `../Assertiva`, ou executá-los e fornecer os outputs | Lentes do Framework aplicadas; sonda AST de testes; controles negativos em todos os achados |
| 2 | Merge das PRs Dependabot #68, #69, #70 e pedido de rebase | Classificador ("Merge Without Review") | 1 | Merge/rebase pelo mantenedor ou permissão explícita | Triagem por PR em [DEPENDABOT_PR_TRIAGE.md](DEPENDABOT_PR_TRIAGE.md) |
| 3 | Habilitar Dependabot alerts e security updates | Configuração do repositório (exige admin) | não tentado | Settings → Code security → Dependabot alerts / security updates | Grupos de segurança já separados no `dependabot.yml` |

Comandos pretendidos após a liberação (a confirmar contra `--help` da versão local):

```text
cd ../Derivanta-Engine && python -m venv .venv && .venv/Scripts/python -m pip install -e .
.venv/Scripts/derivanta-engine inspect ../Prescripta --maintainability --format json
cd ../Assertiva && python -m venv .venv && .venv/Scripts/python -m pip install -e .
.venv/Scripts/assertiva audit ../Prescripta
.venv/Scripts/assertiva audit ../Prescripta --execute
```
