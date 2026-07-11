# Limitações conhecidas

- SQLite e `create_all`, sem migração formal;
- seeds farmacológicos demonstrativos e incompletos;
- nenhuma validação clínica, legal ou regulatória externa;
- nenhuma consulta real a CRM/RQE;
- documentos sem storage binário e OCR produtivo;
- adapters hospitalares mock/FHIR-like, sem contrato real;
- IA externa opcional, com fallback; não há garantia de disponibilidade ou custo;
- filtros JSON do SQLite usam representação textual, embora paginação seja server-side;
- testes frontend ainda não incluem automação visual completa;
- métricas de performance são locais, não SLA.
