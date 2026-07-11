# Relatórios

O Prescripta v0.8.2 possui um motor central de relatórios em
`backend/app/reports`.

## Tipos

- Relatório Técnico de Prescrição.
- Orientações ao Paciente.
- Relatório de Reconciliação Clínica.
- Relatório de Auditoria.
- Relatório simples de Protocolo Rápido, derivado do evento auditado.

## Modos

- `complete_internal`: relatório interno completo, conforme permissão.
- `anonymized`: oculta ou substitui identificadores diretos.
- `patient_friendly`: linguagem simples para paciente.
- `technical_audit`: linguagem técnica com hash, fonte, regra e timeline.

## Fluxo

1. O motor determinístico gera ou recupera a decisão.
2. O `ReportEvidenceBundle` coleta os dados mínimos.
3. O bundle recebe hash estável.
4. O `AIReportComposer` tenta gerar narrativa controlada quando permitido.
5. Se a IA falhar, o fallback determinístico é usado.
6. O renderer gera preview HTML e PDF simples.
7. JSON/CSV exportam dados estruturados.
8. `GeneratedReport` e `AuditEvent` registram metadados e hashes.

## UX v0.8.1

A tela **Relatórios** permite selecionar um item do histórico e abrir:

- metadados de template, versão, IA, prompt, fallback e hashes;
- exportação JSON do relatório gerado;
- regeneração do PDF a partir do alvo auditado;
- link para auditoria filtrada;
- timeline e evidências quando o alvo é uma checagem de prescrição.

## Segurança

Relatórios não exportam API Key, segredo, token ou payload sensível completo.
IA externa recebe dados minimizados por padrão.

## Protocolos v0.8.2

A Central de Protocolos gera preview/PDF simples e exporta JSON/CSV do evento de
execução. O relatório de protocolo não permite que IA altere o fluxo; ele usa a
estrutura fixa do protocolo e os detalhes auditados em `protocol.run`.
