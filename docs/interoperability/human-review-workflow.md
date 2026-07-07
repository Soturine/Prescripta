# Fluxo de Revisão Humana

## Estados

- `pending_review`: lote importado aguardando revisão.
- `accepted`: lote aceito por profissional autorizado.
- `rejected`: lote rejeitado.

## Decisão Por Item

Cada item de reconciliação mostra:

- campo;
- valor atual;
- valor importado;
- fonte;
- confiança;
- badge;
- conflito;
- decisão;
- justificativa.

## Aceite Seguro

O botão de aceite em lote aceita apenas itens sem conflito, sem duplicidade e sem revisão necessária.

Itens conflitantes continuam bloqueados para decisão individual.

## Auditoria

Cada decisão registra:

- usuário;
- data/hora;
- item;
- valor antigo;
- valor importado;
- decisão;
- justificativa opcional;
- fonte original.
