# Guia para TI e integrações

O frontend React consome uma API FastAPI. Serviços concentram regras; Pydantic valida contratos;
SQLAlchemy persiste dados; relatórios compõem EvidenceBundles. Integrações seguem Ports & Adapters:
ports descrevem capacidades, adapters mock convertem payloads FHIR-like/JSON/CSV e reconciliação
grava aceite ou rejeição por item.

Não há scraping de Anvisa, conexão hospitalar real, OCR produtivo ou validação CRM/RQE. Uma fonte
futura exige API oficial/contrato, autenticação, consentimento, minimização, criptografia, retenção,
auditoria e avaliação LGPD. Identificadores externos devem ser mapeados sem substituir dado local
antes da decisão humana.

Para plugar uma fonte, implemente o port, normalize em DTO interno, preserve fonte/versão/data,
crie fila `pending_review`, teste falhas e mantenha fallback. Segredos ficam no backend; nunca em
payload de resposta, log ou `localStorage`. Migrações, PostgreSQL, backup e storage binário estão
planejados para v0.9.0.
