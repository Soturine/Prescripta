# Bloqueios abertos

| # | Ação | Estado | O que destrava | Trabalho independente feito |
|---|---|---|---|---|
| 1 | Instalar e executar Derivanta Engine e Assertiva | **RESOLVIDO** em 2026-11-08: o usuário escolheu adicionar regras de permissão locais (`.claude/settings.local.json`, ignorado pelo Git) para os venvs e CLIs dos dois checkouts | — | Dogfood executado: [DOGFOOD_MATRIX.md](DOGFOOD_MATRIX.md) |
| 2 | Merge das PRs Dependabot #68, #69, #70 | ABERTO: negado pelo classificador ("Merge Without Review"); não retentado | Merge pelo mantenedor | Reavaliadas em 2026-11-08: as três `CLEAN`, todos os checks verdes. #37, #39–#42 seguem conflitadas e vermelhas (ver triagem) |
| 3 | Dependabot alerts e security updates | ABERTO: exige admin | Settings → Code security | Grupos de segurança separados no `dependabot.yml` |
| 4 | Mutação nativa da Assertiva (`--mutate`) no backend | BLOCKED: exige `--execute` com coleta funcional (AS-03, monorepo) e Cosmic Ray instalado no projeto | AS-03 na Assertiva, ou instalar Cosmic Ray e auditar uma cópia autocontida | Mutação manual agent-led: [dogfood/MUTATION_CONTROL.md](dogfood/MUTATION_CONTROL.md) |
| 5 | Playwright via Assertiva | BLOCKED: `spawn cmd.exe ENOENT` no Windows (AS-04) | Correção no adaptador ou execução em Linux | E2E executado diretamente (19 passed / 2 skipped) e no CI |
| 6 | Tag e GitHub Release v1.1.0 | Não iniciado, por instrução do usuário | Auditoria e dogfood concluídos, qualificação do SHA final | Preparação: `6508221` |
