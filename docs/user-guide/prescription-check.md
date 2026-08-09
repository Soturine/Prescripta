# Checagem de prescrição

## Objetivo e acesso

Executar uma análise determinística de segurança medicamentosa. Requer `prescription.check`, paciente acessível e medicamentos cadastrados.

## Etapas

1. **Paciente:** selecione e confirme o contexto clínico.
2. **Medicamentos:** informe itens, dose e via quando aplicável.
3. **Contexto:** revise alergias, função renal, condições e demais dados disponíveis.
4. **Checagem:** envie a análise e aguarde o resultado persistido.
5. **Resultado:** leia risco, alertas, fontes e próximos passos; use o modo técnico quando precisar de detalhes.

## Exemplo e erros comuns

Um alerta de interação crítica exige revisão profissional conforme a política local; ele não autoriza automaticamente troca de terapia. Paciente ausente, medicamento inválido, unidade desconhecida ou falha de API devem ser corrigidos, não ignorados.

## Dados, auditoria, IA e autoridade

A checagem, o bundle de evidências e a decisão clínica determinística são persistidos e auditados. A IA pode explicar um resultado já calculado, sem mudar risco, bloqueio, dose crítica ou recomendação final. O resultado do motor de regras e a decisão profissional registrada são autoritativos.

## Limitações

O resultado depende dos dados disponíveis e não substitui bula, protocolo institucional nem avaliação clínica. Override, quando permitido, exige justificativa e trilha própria.
