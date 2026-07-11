# Quickstart

## Instalação Em Um Caminho

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

## Conferir Saúde

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-install.ps1
```

Ou abra:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:5173`

## Credencial Demo

```txt
admin@prescripta.local
Admin@12345
```

## Reset

```powershell
powershell -ExecutionPolicy Bypass -File scripts/reset-demo-db.ps1
```

O reset recria apenas o banco demo local.
