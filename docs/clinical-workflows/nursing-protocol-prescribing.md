# Prescrição de enfermagem vinculada a protocolo

A v0.8.8 substitui a liberação genérica por uma avaliação explícita de protocolo institucional. A
enfermagem só chega à checagem quando possui `nursing.protocol_prescribe` e `prescription.check`,
vínculo assistencial ativo e uma versão vigente aplicável.

A versão precisa estar ativa, dentro da validade, possuir fonte e revisão humana independente. O
serviço confere instituição, profissão, credencial, região, medicamento, condição, via, faixa de
dose, frequência, duração e parâmetros do paciente. Se o protocolo exigir segunda revisão, o estado
permanece pendente até uma pessoa distinta coassinar.

O resultado informa capacidade, vínculo, protocolo encontrado, aplicabilidade e contexto ausente. A
IA não participa da decisão. Alterar uma definição revisada exige nova versão com novo hash; execução
e negação são auditadas na mesma unidade de trabalho da requisição.

Protocolos e credenciais seed são fixtures demonstrativas. A implementação não afirma aderência a
um conselho, instituição ou serviço real e não autoriza atendimento clínico.
