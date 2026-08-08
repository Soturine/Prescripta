# Workflows profissionais da v0.8.8

## Protocolo institucional e enfermagem

A prescrição por enfermagem permanece bloqueada fora de um protocolo institucional
versionado. A avaliação determinística exige, simultaneamente:

- capacidade `nursing.protocol_prescribe` e `prescription.check`;
- vínculo assistencial ativo e de mesma instituição;
- versão vigente, ativa, com fonte e revisão humana independente;
- profissão, credencial, região e validade compatíveis;
- medicamento, condição, via, dose, frequência, duração e parâmetros do paciente
  dentro do escopo persistido;
- segunda revisão quando configurada pelo protocolo.

O protocolo e cada versão têm identidade própria, hash canônico da definição e eventos
de auditoria. O resultado expõe o estado da capacidade, do vínculo, da aplicabilidade do
protocolo e todo contexto ausente. A IA não participa dessa decisão.

## Intervenção farmacêutica

O workflow persiste problema, recomendação, prioridade, severidade, fontes, snapshot de
dose, autor e instituição. Seu ciclo é `open -> accepted|rejected -> resolved`, com
coassinatura independente opcional, eventos imutáveis por versão, chave idempotente e
controle otimista por `expected_version`.

A decisão é humana e separada da autoria farmacêutica. Nenhuma intervenção altera uma
prescrição automaticamente.

## Reconciliação e formulação

A reconciliação é granular por item. Cada decisão registra estado, ação, justificativa,
autor, versão e histórico, preservando o dado informado na origem. A reconciliação só é
concluída quando não restam itens pendentes ou não resolvidos.

A revisão de formulação reutiliza o contrato dimensional de dose e retorna um resultado
demonstrativo que sempre exige revisão humana. Ela não representa dispensação real nem
gera conduta clínica autônoma.

## Transações e isolamento

Os serviços apenas adicionam dados e executam `flush()`. O limite de commit pertence à
unidade de trabalho da requisição. Consultas e mutações são restritas por instituição e,
para dados de paciente, por capacidade e vínculo assistencial explícito.
