# Guia do usuário

Este guia descreve o Prescripta v0.8.9 por tarefa e rota. A versão canônica é PT-BR; a interface também oferece EN-US. O sistema apoia o trabalho clínico, mas não substitui julgamento profissional, protocolos institucionais, bula validada nem decisão humana.

## Como ler cada página

Cada página informa objetivo, acesso, pré-requisitos, passos, persistência, auditoria, papel da IA, resultado autoritativo e limitações. Quando uma página remete a este contrato, aplicam-se também estas regras:

- o backend valida autorização, escopo de paciente e transições, mesmo que a interface oculte uma ação;
- alertas, níveis de risco, bloqueios e resultados clínicos vêm de regras determinísticas;
- IA pode explicar, classificar ou propor conteúdo sobre fontes fornecidas, nunca decidir risco ou conduta;
- conteúdo de IA e orientações práticas ficam pendentes de revisão quando indicado;
- falhas externas mantêm um fallback explícito e não convertem ausência de evidência em segurança;
- alterações relevantes e acessos sensíveis geram eventos de auditoria sem segredos ou identificadores desnecessários.

## Percursos

- [Primeiro acesso](getting-started.md) e [navegação](navigation.md)
- [Dashboard](dashboard.md), [pacientes](patients.md) e [checagem de prescrição](prescription-check.md)
- [Farmácia clínica](pharmacy.md), [reconciliação](medication-reconciliation.md) e [protocolos](protocols.md)
- [Evidências](evidence.md) e [pesquisa/RWE](research/README.md)
- [Auditoria](audit.md), [assistente de IA](ai-assistant.md) e [permissões](permissions-and-access.md)
- [Idioma](language-and-localization.md) e [glossário](glossary.md)

## Ambiente demonstrativo

Exemplos e dados de demonstração são sintéticos. Não insira CPF, CNS, telefone, endereço, e-mail ou qualquer identificador real em ambientes não aprovados para dados clínicos.
