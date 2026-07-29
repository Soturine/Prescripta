# Assets

- `docs/assets/current/`: screenshots/GIF gerados deterministicamente para a vitrine atual, acompanhados de `manifest.json` com SHA-256, dimensões e peso.
- `docs/assets/v0.8.2/`: captura da release v0.8.2, incluindo protocolos.
- `docs/assets/v0.8.1/`: captura da release v0.8.1.
- Pastas antigas permanecem como histórico visual.

## Inventário v0.8.2

- `dashboard-v0.8.2.png`
- `patients-list-v0.8.2.png`
- `patient-details-v0.8.2.png`
- `medications-catalog-v0.8.2.png`
- `medication-form-v0.8.2.png`
- `prescription-check-v0.8.2.png`
- `patient-guidance-card-v0.8.2.png`
- `imports-reconciliation-v0.8.2.png`
- `reports-list-v0.8.2.png`
- `audit-timeline-v0.8.2.png`
- `ai-settings-v0.8.2.png`
- `protocols-list-v0.8.2.png`
- `protocol-detail-v0.8.2.png`
- `protocol-run-v0.8.2.png`
- `sidebar-version-v0.8.2.png`
- `responsive-view-v0.8.2.png`
- `prescripta-v0.8.2-main-demo.gif`
- `prescripta-v0.8.2-protocols-demo.gif`

Os assets devem ser capturados a partir da aplicação local atual sempre que uma
release alterar UI, fluxos ou textos visíveis.

## Captura corrente

Na raiz do repositório, com dependências backend/frontend e Chromium do Playwright instalados:

```powershell
node scripts/capture-current-assets.mjs
python scripts/check_assets.py
```

O capturador usa banco temporário e seed fictício, aguarda readiness, autentica por cookie HttpOnly,
recusa erros inesperados do navegador, gera o GIF com `ffmpeg` e só substitui `current/` após concluir
todas as capturas e o manifesto. A sondagem anônima inicial de `/api/auth/me` com `401` é a única
exceção específica de console, pois faz parte do bootstrap esperado da tela de login.

Créditos e licenças ficam em `docs/assets/credits.md`.
