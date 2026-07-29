# Autenticação, perfis e autorização

## Sessão

`POST /api/auth/login` valida Argon2, contenção persistente de tentativas e MFA TOTP quando habilitado.
O browser recebe `prescripta_session` HttpOnly, SameSite Lax e com `Secure` fora do modo local.
`GET /api/auth/me` restaura a sessão; `POST /api/auth/logout` remove o cookie. Senha, token, segredo MFA
e API key nunca entram em auditoria ou payload de leitura.

## Profissão, papel e capacidades

Papel não é autorização suficiente. Cada usuário possui profissão, especialidades, status de
credencial demonstrativa e uma lista explícita de capacidades permitidas pelo template profissional.
O backend rejeita capacidades fora do template.

| Perfil | Escopo demonstrativo principal |
| --- | --- |
| `admin` | usuários, catálogo, configuração e governança; sem acesso clínico implícito |
| `medico` | paciente relacionado, checagem, relatório/orientação e override conforme grants |
| `enfermagem` | paciente relacionado e ações permitidas por policy; não prescreve genericamente |
| `farmaceutico` | catálogo e reconciliação/revisão farmacêutica |
| `psicologo` | paciente relacionado e segmento psicológico separado |
| `auditor` | auditoria/relatórios autorizados, sem alteração clínica |
| `clinical_safety_officer` | auditoria e governança de segurança, sem acesso a paciente por papel |

O frontend oculta rotas e ações pela mesma lista de capacidades, mas cada rota FastAPI repete a
checagem e continua sendo a autoridade.

## Autorização por paciente

O acesso exige simultaneamente instituição compatível, capacidade global e uma relação ativa que
cubra objeto, capability e purpose. Relações possíveis:

- grant direto com vigência e revogação;
- participação ativa em care team;
- care episode ativo;
- break-glass temporário e explícito.

Estar no mesmo tenant não concede lista nem leitura. Listagens são filtradas no banco; tentativa
direta sem relação retorna negação sem revelar a existência do objeto. A negação e a operação clínica
compartilham os limites transacionais definidos para evitar auditoria órfã.

Break-glass exige capability, purpose, motivo detalhado, duração curta e chave de idempotência. Pode
ser encerrado, não atravessa tenant e gera eventos de abertura/uso/encerramento. Não remove a
necessidade de revisão institucional.

## Segmentos sensíveis

Conteúdo psicológico usa `patient.sensitive_psychology.read`/write e não é incluído em grants clínicos
genéricos. Administrador, auditor ou profissional da mesma instituição não recebe o segmento por
inferência.

## Dados fictícios

As contas `@prescripta.local` e credenciais exibidas na tela de login existem apenas no seed local.
Ambiente não local rejeita auto-seed, SQLite, CORS local/wildcard e segredos padrão.
