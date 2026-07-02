# Privacidade e LGPD

Prescripta usa dados fictícios e locais no MVP. A versão `v0.2.0` adiciona autenticação e auditoria com usuário responsável, ainda em contexto educacional.

## Dados

- Não use dados reais de pacientes.
- Não versionar banco local.
- Não versionar `.env`.
- Seeds e testes devem permanecer fictícios.
- Credenciais demonstrativas não devem ser reutilizadas fora do ambiente local.

## Princípios

- Minimização de dados.
- Separação entre demonstração e uso real.
- Auditoria de ações sensíveis de checagem.
- Auditoria de criação/edição de pacientes, medicamentos e usuários.
- Senhas nunca devem ser armazenadas em texto puro.

## Próximos Passos

- Cookies seguros ou estratégia equivalente para produção.
- Política de retenção.
- Criptografia e revisão de logs em versões futuras.
