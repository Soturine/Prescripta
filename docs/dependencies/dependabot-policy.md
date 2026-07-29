# Política do Dependabot

## Objetivo

O Dependabot é um sinal de atualização, não uma autoridade de merge. Nenhum PR de dependência é
mesclado automaticamente. Cada candidato é comparado com o `HEAD` real, pesquisado em fontes
oficiais, reproduzido em commit próprio e submetido aos gates do produto.

## Cadência e agrupamento

- execução semanal, às segundas-feiras, no fuso `America/Sao_Paulo`;
- no máximo cinco PRs abertos por ecossistema;
- patches e minors compatíveis são agrupados por ecossistema;
- majors permanecem isolados para revisão de migration guide e breaking changes;
- labels distinguem Python, JavaScript e GitHub Actions;
- o mantenedor `Soturine` é solicitado como reviewer;
- auto-merge não é habilitado.

## Processo de revisão

1. Ler o diff sem fazer checkout da branch do bot.
2. Comparar o `baseRefOid` do PR com a `main` publicada.
3. Consultar release notes, migration guide, advisories, engines, peers e licença em fonte oficial.
4. Confirmar a versão estável atual; títulos antigos não determinam a versão adotada.
5. Implementar a decisão na `main` em commit próprio e atualizar o lockfile com a ferramenta oficial.
6. Executar instalação limpa, lint, testes, build, audits e, quando aplicável, migrations e E2E.
7. Depois da publicação, comentar o commit substituto e fechar o PR sem merge.

## Regras adicionais

- Actions permanecem fixadas por SHA completo verificado contra a tag oficial.
- `pydantic` e `pydantic-core`, React e React DOM são avaliados como pares compatíveis.
- majors de framework, CSS, testes ou infraestrutura são migrações próprias, nunca simples bumps.
- um risco high/critical só pode ser aceito com advisory, escopo, mitigação, responsável, expiração e
  gate automático documentados.
- uma atualização deferida deve registrar condição objetiva para reconsideração.
