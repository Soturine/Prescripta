# Workflow farmacêutico

`PharmacyIntervention` representa um problema e uma recomendação humanos, com prioridade,
severidade, fontes, snapshot de dose, autor, paciente e instituição. O ciclo permitido é
`open -> accepted|rejected -> resolved`.

Cada transição exige `expected_version`, gera evento imutável e usa chave idempotente. Coassinatura
independente pode ser exigida; quem criou não pode satisfazer sozinho essa revisão. A decisão humana
permanece separada da autoria farmacêutica e nenhuma intervenção altera prescrição automaticamente.

A reconciliação continua granular por item e preserva o valor importado. Ela só termina quando não
há item pendente ou não resolvido. A revisão de formulação reutiliza quantidades dimensionais e
sempre retorna necessidade de revisão humana; não representa dispensação real.

Serviços executam `flush()`, enquanto o commit pertence ao request unit of work. Conflito de versão,
negação ou falha de auditoria provoca rollback integral.
