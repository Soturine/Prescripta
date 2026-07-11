# Versionamento e compatibilidade de integrações

Adapters declaram `source_system`, versão do payload e mapeamento aplicado. Campos desconhecidos
são preservados somente quando seguros; campos obrigatórios ausentes bloqueiam a aplicação.

Mudança incompatível exige nova versão de contrato e período explícito de transição. Exemplos são
fictícios e FHIR-like: não alegam conformidade FHIR certificada nem conexão hospitalar real.
