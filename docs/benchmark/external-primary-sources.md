# Referências externas e benchmarks

Consulta realizada em **29 de julho de 2026**. Esta lista separa padrões e obrigações de benchmarks
de produto. Referenciar uma fonte não torna o Prescripta conforme, certificado ou validado.

## Padrões e segurança do paciente

| Fonte oficial | Estado consultado | Uso no Prescripta |
| --- | --- | --- |
| [HL7 FHIR](https://hl7.org/fhir/versions.html) | R5 `5.0.0`, versão publicada atual | benchmark de recursos, provenance e versionamento; adapters atuais são apenas FHIR-like |
| [SMART App Launch](https://hl7.org/fhir/smart-app-launch/) | `2.2.0`, STU 2.2 sobre FHIR R4 | benchmark futuro de OAuth, escopos e launch context; não implementado |
| [CDS Hooks](https://cds-hooks.hl7.org/2.0/) | release publicada `2.0` | benchmark de discovery, hooks, cards, feedback e override; endpoint atual não é conforme |
| [WHO Medication Without Harm](https://www.who.int/initiatives/medication-without-harm) | desafio global e framework vigentes | prioriza polifarmácia, situações de alto risco e transições de cuidado |
| [ONC SAFER Guides](https://healthit.gov/clinical-quality-and-safety/safer-guides/) | conjunto atualizado em 2025, oito guias | benchmark de autoavaliação, resiliência, contingência e segurança de EHR |

FHIR R5 é um padrão amplo e misto entre conteúdo normativo e STU. A própria licença/advertência do
FHIR exige que implementadores avaliem adequação ao uso. Por isso, serializar um `Bundle` ou imitar
nomes de recursos não autoriza o claim “FHIR completo”. CDS Hooks 2.0, por sua vez, exige contratos
de discovery/service/feedback e semântica de hook que o Prescripta não oferece.

## Brasil: regulação e exercício profissional

| Fonte oficial | Estado consultado | Consequência |
| --- | --- | --- |
| [Anvisa — SaMD e RDC 657/2022](https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa/2022/software-como-dispositivo-medico-perguntas-e-respostas/) | orientação oficial vigente consultada | qualquer finalidade diagnóstica/terapêutica exige análise formal de enquadramento; não realizada |
| [Anvisa — dispositivos médicos](https://www.gov.br/anvisa/en/regulation-of-products/medical-devices) | lista RDC 657/2022 para SaMD e RDC 751/2022/alterações para dispositivos | obrigação potencial, não benchmark técnico opcional |
| [Cofen — Resolução 801/2026](https://www.cofen.gov.br/resolucao-cofen-no-801-de-14-de-janeiro-de-2026/) | diretrizes atuais para prescrição por enfermeiros | não presumir proibição geral; exigir processo de enfermagem, protocolo/programa, instituição e rastreabilidade |
| [CFP — registro documental](https://transparencia.cfp.org.br/crp12/pergunta-frequente/registro-documental/) | Resolução CFP 001/2009 e orientações correlatas | registrar apenas o necessário em prontuário multiprofissional e segregar material de acesso restrito |

O Prescripta não passou por enquadramento Anvisa, validação com conselhos, comitê de ética, DPO,
assessoria jurídica ou instituição de saúde. Esses itens são bloqueadores externos para uso real.

## Engenharia e segurança

| Fonte oficial | Versão/edição | Aplicação |
| --- | --- | --- |
| [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x00-toc/) | edição 2023 | BOLA/BFLA, autenticação, consumo de recursos, SSRF, configuração e consumo seguro de APIs |
| [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final) | versão 1.1 | provenance, revisão, dependências, resposta a vulnerabilidades e gates reprodutíveis |

Os controles implementados reduzem riscos, mas não equivalem a certificação OWASP/NIST.

## Projetos de referência

| Projeto oficial | Estado em 29/07/2026 | Lição, sem cópia arquitetural |
| --- | --- | --- |
| [HAPI FHIR](https://hapifhir.io/hapi-fhir/docs/) | documentação exibindo `8.12.0` | validação, multitenancy, autorização, consentimento, paginação e servidor FHIR exigem subsistemas próprios |
| [OpenMRS](https://openmrs.org/download/) | Reference App `3.7.1`; Platform `2.8.1` | modularidade, frontend por extensão, REST/FHIR e terminologia são capacidades de plataforma madura |
| [OpenEMR](https://www.open-emr.org/releases/) | estável `8.2.0`, 08/07/2026 | release, checksums, hardening, SMART/FHIR e certificação têm governança contínua |
| [Bahmni](https://bahmni.atlassian.net/wiki/spaces/BAH/pages/5519474693/Bahmni%2BSecurity%2BPatch%2BJuly%2B02%2B2026%2BRelease%2BNotes) | patches `1.0.2-lite`/`1.0.2-standard` em 02/07/2026 | composição de sistemas exige inventário, compatibilidade, upgrade e resposta coordenada a CVEs |

Nenhum código ou dependência foi copiado desses projetos. Licenças e contexto operacional impedem
adotar componentes apenas por popularidade. Eles servem para evidenciar a distância entre uma demo
educacional e um EHR/HMIS ou servidor FHIR operacional.
