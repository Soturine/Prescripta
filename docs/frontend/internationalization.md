# Internacionalização

## Escopo

PT-BR é o locale canônico e EN-US é suportado na interface. A arquitetura aceita novos catálogos, como `es-419`, sem tradução por IA em runtime.

## Resolução

1. escolha manual persistida;
2. lista de idiomas preferidos do navegador;
3. idioma principal do navegador;
4. fallback PT-BR.

O locale atualiza `document.documentElement.lang`. A preferência salva contém apenas o código de idioma e não é evento clínico.

## Contrato semântico

Catálogos traduzem rótulos, instruções, estados humanos e mensagens. Não traduzem códigos clínicos, unidades, identificadores de fonte, valores canônicos de enum ou conteúdo regulatório. Datas e números usam `Intl`; o backend mantém contratos estáveis e não recebe textos localizados como decisão.

## Quality gates

`scripts/check_i18n_catalogs.mjs` falha em chave ausente ou órfã, placeholders divergentes e texto literal nas superfícies migradas. Testes verificam fallback, persistência, equivalência de status e troca sem alteração de autorização. Playwright e screenshots representativos cobrem PT-BR e EN-US.

## Glossário

A terminologia de produto está no [glossário do usuário](../user-guide/glossary.md). Termos técnicos preservam o original quando a tradução puder criar ambiguidade.
