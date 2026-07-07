# Autenticação e Perfis

Prescripta usa autenticação JWT e autorização por perfil.

## Endpoints

- `POST /api/auth/login`
- `GET /api/auth/me`

## Perfis

- `admin`: gerencia pacientes, medicamentos, usuários, checagens, importações, auditoria, dashboard e configuração de IA.
- `medico`: gerencia pacientes, consulta medicamentos, verifica prescrições, usa IA configurada e revisa resumos/importações permitidos.
- `enfermagem`: consulta pacientes e medicamentos, verifica prescrições, visualiza orientações e usa IA configurada.
- `auditor`: visualiza dashboard, auditoria, importações, reconciliação e status da IA, sem alterar dados.

## IA

- Somente `admin` salva, apaga, testa e ativa provider/modelo de IA.
- Médicos, enfermagem e auditores podem ver status de IA habilitada/desabilitada.
- Nenhum perfil recebe API Key em resposta.
- Auditoria registra eventos técnicos sem segredo.

## Importações

- `admin` e `medico`: importar, aceitar/rejeitar lotes e decidir itens de reconciliação.
- `enfermagem`: visualizar importações conforme regras existentes.
- `auditor`: visualizar importações, reconciliação e auditoria.

## Segurança

Senhas são armazenadas com hash Argon2. A senha original nunca deve ser salva, retornada em API, registrada em log ou enviada para auditoria.

O segredo do JWT é configurado por `PRESCRIPTA_SECRET_KEY`.

O frontend usa `localStorage` para token de sessão no MVP local. API Keys de IA nunca usam `localStorage`.

## Credenciais De Exemplo

- `admin@prescripta.local` / `Admin@12345`
- `medico@prescripta.local` / `Medico@12345`
- `enfermagem@prescripta.local` / `Enfermagem@12345`
- `auditor@prescripta.local` / `Auditor@12345`

Essas contas existem apenas para demonstração local.
