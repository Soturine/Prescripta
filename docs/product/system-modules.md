# Módulos do sistema

| Módulo | Entrada | Saída | Regra de segurança |
| --- | --- | --- | --- |
| Dashboard | contagens e status | métricas operacionais/catalogais | não representa cobertura clínica |
| Pacientes | dados fictícios | perfil, histórico, bundle | dado ausente permanece explícito |
| Medicamentos | catálogo e fontes | produto, dose, policy, counseling | novo dado fica pendente |
| Checagem | paciente + exposição | risco, dose, sinais e policy | IA não altera resultado |
| Protocolos | versão + contexto | execução e relatório | IA não cria etapa |
| Importações | JSON/CSV/FHIR-like | reconciliação por item | aplicação depende de aceite humano |
| Relatórios | EvidenceBundle | preview/PDF/JSON/CSV | hash e fallback registrados |
| Auditoria | eventos | filtros, timeline, evidência | leitura restrita a admin/auditor |
| IA | bundle minimizado | explicação/extração | schema e source locking |
| Usuários | role + perfil demo | autorização e policy | CRM/RQE não verificados |
