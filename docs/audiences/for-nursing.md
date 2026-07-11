# Guia para enfermagem

Enfermagem pode visualizar pacientes, registrar dados e perfil funcional nos fluxos autorizados,
acompanhar protocolos demonstrativos e ler orientações revisadas. Não pode alterar regra de risco,
dose final, política, status validado ou liberar prescrição; o backend aplica essa autorização.

Antes de escalar, procure peso/altura/idade, alergias, medicamentos atuais, condição renal/hepática,
gestação/lactação, uso de álcool, quedas, direção/máquinas e documentos pendentes. Dados ausentes
devem ser registrados como desconhecidos, nunca inferidos.

Orientações ao paciente permanecem `pending_review` até revisão humana. Em protocolo, registre a
execução factual e o responsável, sem transformar uma explicação da IA em conduta. Alertas altos,
mudança clínica, divergência de medicação ou dúvida de dose devem ser escalados ao prescritor e à
equipe farmacêutica conforme o processo institucional.

## Passo a passo e exemplo

Revise peso/altura, medicamentos, alergias e perfil funcional; registre “não informado” quando não
souber; leia a orientação revisada; escale risco alto/crítico. Exemplo: sedativo em motorista
profissional pede comunicação e revisão, não suspensão automática pela interface.

## O que você vê — e o que não significa

Cards clínicos mostram ação e lacunas. JSON técnico não aparece por padrão. Um alerta não é ordem
de administração nem diagnóstico, e uma orientação gerada não substitui prescrição vigente.

## FAQ, glossário e links

**Posso revisar laudo?** Apenas conforme role e fluxo autorizado. **Posso alterar policy?** Não.
“Escalonar” é encaminhar ao responsável habilitado. Veja [fluxos](../product/clinical-workflows.md) e
[limitações](../product/known-limitations.md).
