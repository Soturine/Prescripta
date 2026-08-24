# Assets de documentação

## Política de diretórios

- `docs/assets/current/` é a vitrine evergreen do `main`: 10 PNGs, um GIF e `manifest.json`.
- `docs/assets/vX.Y.Z/` preserva a vitrine histórica da release publicada correspondente.
- diretórios legados sem manifesto permanecem apenas como registro histórico e não representam o
  produto atual.

O README principal deve usar somente `current/`. Uma captura pós-release nunca deve sobrescrever
`v1.0.0/` ou outro diretório versionado publicado.

## Recaptura da vitrine corrente

Pré-requisitos exclusivos da geração visual: dependências backend/frontend, Chromium do Playwright e
`ffmpeg`. Eles não são necessários para uma pessoa que apenas executa a aplicação pelo Compose.

Na raiz do repositório:

```powershell
node scripts/capture-current-assets.mjs
python scripts/check_assets.py
```

O capturador inicia a aplicação real com banco temporário e seed sintético, aguarda readiness,
autentica por cookie HttpOnly, captura PT-BR, uma evidência EN-US e navegação móvel, e monta o GIF com
frames atuais. Ele recusa erros inesperados do navegador; o `401` anônimo inicial de `/api/auth/me`
é a exceção esperada durante o bootstrap do login.

Como o capturador lê `VERSION`, ele também pode escrever em `docs/assets/v<versão>/`. Se essa versão
já estiver publicada, preserve ou restaure o diretório histórico e aceite apenas as mudanças em
`current/`.

## Manifesto e revisão

`current/manifest.json` registra versão, SHA-256, dimensões e tamanho de cada asset. Antes do commit:

1. confirme ausência de loading, modal/toast acidental, clipping, erro ou segredo;
2. confirme que todos os dados são fictícios e que PT-BR, EN-US e mobile são legíveis;
3. execute `python scripts/check_assets.py`;
4. confira no diff que nenhum diretório histórico publicado foi alterado.

Créditos e licenças ficam em [credits.md](credits.md).
