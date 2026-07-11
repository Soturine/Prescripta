# Onboarding Institucional

Prescripta foi preparado para acoplamento institucional, mas nao acessa sistemas
hospitalares sem API, contrato, permissao e configuracao.

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
6. Ativar auditoria e revisao humana.
7. Documentar fonte, jurisdicao, status de validacao e fallback.

## O Que Nao Fazer

- Nao fazer scraping agressivo.
- Nao automatizar login em portal.
- Nao importar dado real sem permissao e seguranca.
- Nao prometer integracao automatica.
- Nao permitir que IA altere dado importado sem revisao humana.
