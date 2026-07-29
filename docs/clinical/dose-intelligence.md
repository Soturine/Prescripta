# Dose Intelligence

O motor calcula apenas quando a regra possui fonte e status. Fórmula, base antropométrica, inputs,
unidade, frequência, duração e via permanecem rastreáveis. Dose por administração, diária,
cumulativa e por procedimento não são comparadas entre dimensões incompatíveis.

Na v0.8.7, `Quantity`/`UnitDefinition` normalizam massa (`mcg`, `mg`, `g`), volume (`mL`, `L`), tempo,
taxas e bases corporais com `Decimal` e fatores racionais. Quantidade em volume só produz massa quando
há concentração compatível; se um volume duplicado for enviado, ele precisa ser equivalente à
quantidade administrada. Intervalo pode derivar frequência, mas PRN usa exclusivamente seu teto de
administrações. Infusão contínua exige taxa explícita.

Arredondamento usa a policy `prescripta-half-even-v1`, precisão rastreada e nunca converte para `float`
no caminho decisório. Limite com unidade ausente/incompatível, concentração ambígua, duração
incompleta ou conversão não provada produz `not_calculable`/dados insuficientes, não zero nem resultado
favorável.

Peso e altura fora das faixas operacionais, frequência inválida, rota divergente ou fonte ausente
produzem dados insuficientes. Regras demonstrativas continuam pendentes de validação humana. IA
pode explicar o resultado estruturado, nunca alterar cálculo, limite ou status.
