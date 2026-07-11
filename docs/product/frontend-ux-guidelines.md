# Diretrizes de UX do Frontend

## Objetivo

Prescripta deve parecer um produto healthtech maduro: claro, responsivo,
rastreável e rápido de ler. A UI não deve esconder riscos clínicos atrás de
decoração.

## Princípios

- Hierarquia visual antes de densidade.
- Cards para itens repetidos ou painéis reais, não para cada seção da página.
- Botões com ícones para ações claras.
- Estados vazios e loading úteis.
- Texto curto em painéis operacionais.
- Fonte, status e auditoria sempre visíveis quando influenciam confiança.

## Padrões v0.8.2

- `field`, `btn-primary`, `btn-secondary`, `surface-card` e `skeleton-line` ficam
  no CSS global.
- Sidebar é responsiva, com rolagem horizontal em telas estreitas.
- Telas novas devem funcionar em notebook, tablet e mobile estreito.
- Transições são leves: hover, foco, loading e expansão visual sem exagero.

## Protocolos

A tela de Protocolos usa:

- lista filtrável;
- badge de severidade;
- contexto mínimo;
- passos marcáveis;
- painel de fonte/evidência;
- execução auditada;
- preview de relatório.

## Limites

Não usar imagens externas como substituto de UX. Assets devem ajudar
documentação, onboarding ou empty states e precisam de crédito quando externos.
