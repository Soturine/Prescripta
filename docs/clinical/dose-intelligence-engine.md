# Dose Intelligence Engine

## Finalidade

O motor calcula uma referência rastreável a partir de uma regra cadastrada; ele não escolhe a dose
do paciente. A resposta separa valor prescrito, faixa usual, teto, fórmula, unidade, base corporal,
dados faltantes, fonte e status de validação.

## Bases e fórmulas

- **Fixa:** usa a faixa da regra sem multiplicador antropométrico.
- **Peso real:** `dose por kg × peso atual`.
- **Peso ideal:** fórmula de Devine demonstrativa, dependente de altura e contexto informado.
- **Peso ajustado:** `PI + 0,4 × (peso real − PI)`.
- **Massa magra:** estimativa demonstrativa registrada nos dados usados.
- **Superfície corporal:** Mosteller, `√((altura em cm × peso em kg) / 3600)`.

Unidades não são convertidas implicitamente. `mg/kg/dia`, `mg/m²`, `mcg/kg/min` e outras regras
devem declarar período e unidade. Peso ou altura ausentes produzem `insufficient_data`, nunca zero.

## Interpretação

`within_usual_range`, `below_usual_range`, `above_usual_range` e `above_maximum` comparam a
prescrição à regra. Regras `demo_seed` ou `pending_review` sempre exigem revisão humana, mesmo
quando o cálculo cai na faixa. Para anestésicos locais, o teto por procedimento é avaliado
separadamente do teto diário.

### Matemática da faixa usual

A faixa possui agora contrato explícito: `usual_low`, `usual_high`, `usual_dose_unit` e
`usual_range_scope`. O escopo aceito é `per_administration`, `daily` ou `rate`. Compatibilidade com
regras antigas usa `dose_unit` como unidade declarada e `daily` como escopo; cadastro novo não deve
depender desse fallback.

Antes de classificar, o motor:

1. interpreta os dois limites como quantidades dimensionais independentes;
2. aplica a mesma base corporal provada aos limites por kg ou m²;
3. normaliza ambos para uma unidade absoluta comum (`mg`, `mg/day` ou `mg/h`, por exemplo);
4. normaliza a quantidade prescrita para essa mesma dimensão;
5. verifica `low <= high` sem arredondamento de apresentação;
6. classifica com limites inclusivos:

```text
prescribed < low   -> below_usual_range
low <= prescribed <= high -> within_usual_range
prescribed > high  -> above_usual_range
```

Teto absoluto, diário, de procedimento, cumulativo ou de taxa mantém precedência sobre a faixa
usual. Em PRN, compara-se o teto diário declarado, nunca uma exposição exata presumida. Unidade
ausente/incompatível, limites invertidos ou base corporal ausente produzem abstention, não resultado
favorável. `Decimal` não arredondado é a autoridade da comparação; `prescripta-half-even-v1` afeta
somente a apresentação.

## Limites

Fórmulas demonstrativas não substituem bula, ajuste renal/hepático, diluição, velocidade de
infusão, protocolo de anestesia ou julgamento clínico. A IA pode extrair uma candidata a regra de
uma fonte recuperada, mas não pode ativá-la nem alterar o resultado calculado.
