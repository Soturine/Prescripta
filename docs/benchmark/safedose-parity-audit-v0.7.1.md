# Auditoria de Paridade Conceitual SafeDose/RicoToro - v0.7.1

Esta auditoria usa SafeDose/RicoToro apenas como benchmark conceitual. Não houve cópia de código, texto, CSS, estrutura, banco ou fluxo proprietário.

| Item avaliado | Status Prescripta | Observação |
| --- | --- | --- |
| Streamlit/app único | Prescripta possui melhor | Prescripta usa frontend React + backend FastAPI separados. |
| Uso de Gemini | Prescripta possui parcialmente | Gemini é provider configurável, mas depende de chave/modelo válidos. |
| Prontuários/pacientes | Prescripta já possui | CRUD de pacientes, perfil clínico, identificadores e histórico funcional. |
| Criptografia | Prescripta possui parcialmente | API Key de IA pode ser criptografada; banco clínico ainda é SQLite local. |
| Login | Prescripta já possui | JWT com perfis. |
| Pacientes | Prescripta já possui | Pacientes, triagem rápida e perfil clínico. |
| Medicamentos | Prescripta já possui | Catálogo com princípio ativo, aliases, fonte e regras. |
| Interações | Prescripta já possui | Motor determinístico e regras cadastradas. |
| Alergias | Prescripta já possui | Bloqueio determinístico por alergia. |
| Central de emergência | Prescripta não possui | Roadmap futuro, não implementado na v0.7.1. |
| Protocolos PCR | Não será implementado agora | Exige fonte/protocolo validado e validação clínica. |
| Anafilaxia | Não será implementado agora | Roadmap futuro. |
| IAM | Não será implementado agora | Roadmap futuro. |
| Crise convulsiva | Não será implementado agora | Roadmap futuro. |
| Sugestão de alternativa por IA | Prescripta possui melhor | Alternativas vêm de base cadastrada e passam pelo motor de risco; IA não decide. |
| Auditoria/logs | Prescripta já possui | Auditoria de prescrição, usuários, importação, reconciliação e IA. |
| Dashboard/admin | Prescripta já possui | Dashboard, usuários e permissões. |
| Cache de IA | Prescripta possui parcialmente | Cache de modelos e fallback; não há cache de resposta clínica externa. |

## Lacunas Relevantes

- Central de emergência/protocolos rápidos.
- Criptografia abrangente de banco clínico fora do escopo atual.
- Relatórios/exportação e auditoria avançada.
- Deploy com PostgreSQL/migrações.

## Roadmap

- `v0.8.0`: relatórios, exportação e auditoria avançada.
- `v0.8.x`: protocolos rápidos/emergência se houver fonte validada e escopo clínico revisado.
- `v0.9.0`: Docker/PostgreSQL/deploy.
