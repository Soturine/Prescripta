# Idioma e localização

## Objetivo e opções

A interface oferece PT-BR e EN-US sem alterar os dados clínicos. A resolução segue escolha manual persistida, idiomas preferidos do navegador e fallback para PT-BR.

## Passos

1. Abra o seletor de idioma no login ou cabeçalho.
2. Escolha **Português (Brasil)** ou **English (US)**.
3. Confirme títulos, navegação, estados e mensagens da tarefa.
4. Reporte texto não traduzido com rota e contexto.

## Exemplo e erros comuns

Trocar para EN-US traduz “Pendente” para “Pending”, mas não muda o valor persistido do status. Códigos, nomes próprios, DCB e conteúdo de uma fonte podem permanecer no idioma original.

## Dados, auditoria, IA e autoridade

Somente a preferência de locale fica no navegador; nenhuma decisão clínica muda. A troca de idioma não exige evento clínico de auditoria. A IA não traduz valores autoritativos. Valores canônicos do backend e suas regras são autoritativos.

## Limitações

A documentação canônica permanece PT-BR nesta versão. Formatos regulatórios e terminologia devem respeitar fonte e jurisdição.
