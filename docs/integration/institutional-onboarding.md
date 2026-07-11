# Onboarding Institucional

Prescripta foi preparado para acoplamento institucional, mas não acessa sistemas
hospitalares sem API, contrato, permissao e configuração.

## Caminhos De Integracao

- `HospitalPatientAdapter`: pacientes, identificadores e dados demograficos.
- `HospitalMedicationAdapter`: medicamentos, principios ativos, produtos e
  aliases.
- `HospitalExamAdapter`: exames, valores laboratoriais e observacoes.
- `HospitalPrescriptionAdapter`: prescricoes, itens, dose, via e duracao.
- `HospitalDocumentAdapter`: laudos, PDFs, imagens, FHIR DocumentReference e
  documentos internos.

## Formatos

- FHIR-like.
- JSON.
- CSV.
- API custom.
- Banco institucional.
- Mock adapter.
- Upload manual.

## Passos De Implantacao

1. Validar contrato, base legal, LGPD e responsaveis.
2. Mapear identificadores e regras de consentimento.
3. Mapear pacientes, medicamentos, exames, laudos e prescricoes.
4. Configurar adapters em ambiente de homologacao.
5. Testar com dados artificiais ou anonimizados.
6. Ativar auditoria e revisão humana.
7. Documentar fonte, jurisdição, status de validação e fallback.

## O Que Não Fazer

- Não fazer scraping agressivo.
- Não automatizar login em portal.
- Não importar dado real sem permissao e segurança.
- Não prometer integracao automatica.
- Não permitir que IA altere dado importado sem revisão humana.
