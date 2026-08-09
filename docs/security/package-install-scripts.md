# Inventário de install scripts npm

Revisado em 9 de agosto de 2026. Os validadores Python e Node em `scripts/check_install_scripts.*`
comparam o lockfile com os caminhos e versões exatos de `scripts/install-script-policy.json`;
pacote novo, remoção ou mudança de versão exige nova revisão. Não há wildcard. O validador Node
também executa dentro do estágio de build da imagem frontend, antes de `npm ci`.

| Pacote | Versão | Script/finalidade | Relação | Fonte | Decisão | Risco |
| --- | --- | --- | --- | --- | --- | --- |
| `esbuild` | 0.28.1 | `install.js` seleciona/verifica o binário de plataforma usado por Vite | transitiva/dev | pacote npm com integrity no lock | permitido para build; versão exata | execução durante `npm ci`; mitigada por lock, integrity e gate |
| `fsevents` | 2.3.3 | instalação nativa opcional para eventos de filesystem no macOS | transitiva/dev/opcional | pacote npm com integrity no lock | permitido somente no path exato | não instalado em Linux/Windows; revisar mudança |
| `playwright/fsevents` | 2.3.2 | variante transitiva opcional do Playwright para macOS | transitiva/dev/opcional | pacote npm com integrity no lock | permitido somente no path exato | não instalado em Linux/Windows; revisar mudança |

O npm usado pelo projeto não oferece uma allowlist nativa equivalente por pacote no lock atual.
`ignore-scripts=true` quebraria a instalação verificada do binário do esbuild; por isso o controle é
fail-closed sobre `hasInstallScript`, antes da instalação nos workflows.
