# Troubleshooting

## Frontend Não Abre

- Rode `cd frontend && npm install`.
- Confirme se a porta `5173` está livre.
- Ajuste `VITE_API_URL` se o backend estiver em outra porta.

## Backend Não Sobe

- Confirme Python 3.12.
- Rode `.\.venv\Scripts\python -m pip install -r backend\requirements.txt`.
- Verifique `.env` e `PRESCRIPTA_DATABASE_URL`.

## Login Falha

- Rode `scripts/reset-demo-db.ps1`.
- Confirme `PRESCRIPTA_AUTO_SEED=true`.
- Use uma das credenciais demo do README.

## IA Externa Indisponível

- Isso não bloqueia o produto.
- O fallback local deve continuar funcionando.
- Em **IA**, confira provider, modelo, chamada externa e circuit breaker.

## PDF Com Caracteres Estranhos

O renderer simples usa sanitização para preservar acentos compatíveis com
`cp1252`. Se um caractere não suportado aparecer, substitua por pontuação simples
ou amplie a tradução em `backend/app/reports/pdf_renderer.py`.

## Protocolos Não Executam

- Perfis auditor podem consultar, mas não registrar execução.
- Preencha campos obrigatórios marcados com `*`.
- Lembre que os protocolos são demonstrativos e exigem decisão humana.
