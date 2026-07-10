# Privacidade em Relatórios com IA

Relatórios podem usar o provider ativo em **IA**, mas a chamada externa recebe
somente dados minimizados.

Não enviar para IA externa:

- CPF;
- CNS;
- telefone;
- endereço;
- e-mail;
- documento;
- identificador externo real;
- número de convênio;
- registro hospitalar real;
- API Key, token ou segredo.

O backend substitui referência identificável por pseudônimo antes de chamar IA
externa. O relatório interno pode exibir dados permitidos ao usuário autorizado,
mas isso não muda o payload enviado ao provider.

Fallback:

- provider indisponível;
- chamada externa desabilitada;
- JSON inválido;
- campo reservado retornado;
- `source_id` inventado;
- erro de rede ou timeout.

Nesses casos, a narrativa determinística é usada e o evento registra fallback.
