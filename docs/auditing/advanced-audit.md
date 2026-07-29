# Auditoria Avançada

A v0.8.0 amplia a auditoria para cobrir relatórios e exportações.

Filtros:

- usuário;
- perfil;
- paciente;
- medicamento;
- princípio ativo;
- tipo de evento;
- risco;
- status;
- severidade;
- provider e modelo de IA;
- fallback;
- fonte;
- jurisdição;
- data inicial e final;
- texto livre.

A tela `/audit` permite filtrar, limpar filtros, exportar JSON, exportar CSV,
gerar PDF e abrir detalhe de evento com timeline e evidências.

Eventos novos:

- `prescription.alert_fired`;
- `report.generated`;
- `report.pdf_downloaded`;
- `export.json`;
- `export.csv`.
