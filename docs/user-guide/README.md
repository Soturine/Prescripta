# Guia do usuário

Este guia descreve o Prescripta v1.0.0 por tarefa e rota. A versão canônica é PT-BR; a interface também oferece EN-US. O sistema apoia o trabalho clínico, mas não substitui julgamento profissional, protocolos institucionais, bula validada nem decisão humana.

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

## Sequência recomendada para a demo

1. inicie por Docker ou pelo setup local e entre com um [perfil demo](../../README.md#primeiro-uso-e-perfis-demo);
2. use **Visão geral** para reconhecer tarefas e pendências do papel;
3. abra **Pacientes** e revise o workspace longitudinal sintético;
4. consulte **Medicamentos** e execute uma **Checagem clínica**;
5. com perfil autorizado, explore **Farmácia clínica**, reconciliação e **Protocolos**;
6. consulte relatórios, **Evidências** e o workspace de **Pesquisa e RWE**;
7. confirme a trilha em **Auditoria**, altere PT-BR/EN-US e encerre a sessão;
8. quando necessário, recrie o seed local pelo [troubleshooting](../setup/troubleshooting.md).

## Ambiente demonstrativo

Exemplos e dados de demonstração são sintéticos. Não insira CPF, CNS, telefone, endereço, e-mail ou qualquer identificador real em ambientes não aprovados para dados clínicos.
