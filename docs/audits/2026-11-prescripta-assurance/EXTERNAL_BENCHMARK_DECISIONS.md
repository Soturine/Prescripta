# Benchmark externo e decisões — 2026-11-08

Pesquisa de leitura e análise. Nenhum código, documentação proprietária ou interface protegida foi
copiado. Nenhuma integração real com terceiros é afirmada. "Consultado" = fonte lida nesta rodada;
"indexado" = conteúdo obtido por resumo de busca porque a página original recusou acesso (HTTP 403).

## 1. Alertas de tecnovigilância (Anvisa) sobre CPOE — convertidos em testes

| Alerta | Data | Classe de falha (pública) | Fonte | Situação no Prescripta | Teste |
|---|---|---|---|---|---|
| 4612 — Tasy EMR | 2024 | erro de **conversão de unidade** em protocolos gerando cálculo errado | [Anvisa, listagem de alertas](http://antigo.anvisa.gov.br/en/resultado-de-busca?p_p_id=101&p_p_lifecycle=0&p_p_state=maximized&p_p_mode=view&p_p_col_id=column-1&p_p_col_count=1&_101_struts_action=/asset_publisher/view_content&_101_assetEntryId=6869577&_101_type=content&_101_groupId=33868&_101_urlTitle=alerta-4612-tecnovigilancia-comunicado-da-empresa-philips-medical-systems-ltda-tasy-emr-&inheritRedirect=true) (indexado) | **REFUTED para o HEAD**: conversões de massa são exatas (frações), aliases de micrograma corretos, dimensões incompatíveis e unidades desconhecidas (mEq, mmol, UI, %) não convertem | `tests/test_tecnovigilance_scenarios.py` (propriedade de ida e volta exata + 18 casos) |
| 4614 — Tasy EMR | 2024 | número decimal exibido **sem zero antes da vírgula**, risco de dose incorreta | [Anvisa](http://antigo.anvisa.gov.br/listagem-de-alertas/-/asset_publisher/R6VaZWsQDDzS/content/alerta-4614-tecnovigilancia-comunicado-da-empresa-philips-medical-systems-ltda-tasy-emr-/33868?inheritRedirect=false) (indexado) | Zero à esquerda já presente. **Mas a mesma classe (exibição ambígua de dose) foi encontrada**: alertas do backend em notação científica (`1.2E+3 mg`, NEW-13) e frontend arredondando `0,0005 mg → 0,001 mg` (NEW-14) | `test_dose_display_unambiguous.py` (propriedade: ida e volta exata, sem expoente); `formatters.test.ts` |
| 5063 — Tasy EMR/Delphi/Java | out/2025 | ausência de alerta para **concentração de eletrólito acima do máximo** (ex.: KCl em diálise peritoneal, CPOE) | [Anvisa](http://antigo.anvisa.gov.br/listagem-de-alertas/-/asset_publisher/R6VaZWsQDDzS/content/alerta-5063-tecnovigilancia-comunicado-da-empresa-philips-medical-systems-ltda-tasy-emr-10216710404-tasy-delphi-10216710405-tasy-java-10216710403-/33868?inheritRedirect=false) (indexado); [Carta ao cliente](http://antigo.anvisa.gov.br/documents/33868/7153431/Carta+ao+Cliente/b0b5fded-0e61-4154-876f-51b460ca47f1) | Limite em unidade não suportada (mEq) já falha fechado (alerta HIGH, sem decisão favorável). **Lacuna real (NEW-15):** não existe regra de concentração máxima; a cobertura dizia "dose avaliada". Agora a concentração informada vira `concentration_limit` não avaliado e impede conclusão favorável | idem, `test_concentration_without_ceiling_rule_is_declared_not_evaluated` |

## 2. Philips Tasy EMR — o que é publicamente verificável

| Tema | Evidência pública | Fonte |
|---|---|---|
| Arquitetura | Web, banco Oracle; cliente fala com o serviço por **API REST proprietária**; serviço de integração separado para HL7, SOAP, REST e arquivos | [Oracle Architecture Center — Implement the Philips Tasy Healthcare System](https://docs.oracle.com/en/solutions/implement-philips-tasy-healthcare-system/index.html) |
| Escopo clínico | Do cadastro e documentação até **CPOE** e **reconciliação medicamentosa** | [Brochura Philips Tasy EMR](https://www.philips.com/c-dam/b2bhc/br/marketing/philips_tasy_emr_general_brochure.pdf) |
| Ecossistema | Integração com parceiros de prescrição eletrônica, assinatura e certificação (Mevo, Memed, CertiSign, Soluti, ForSign) | [Futuro da Saúde](https://futurodasaude.com.br/philips-tasy-integracao-parceiros/) |
| Interoperabilidade Philips | IntelliBridge Enterprise: HL7 v2, FHIR, DICOM; "orders inbound from CPOE" — produto separado; não confirmado como caminho do Tasy | [Philips IntelliBridge Enterprise](https://www.philips.com.au/healthcare/product/HC866183/intellibridge-enterprise-interoperability-solution) |
| Não encontrado | API FHIR pública do Tasy; detalhes do módulo de farmácia; rastreabilidade das regras de CDS | — |

## 3. Posicionamento e decisões

Prescripta **não** deve tentar ser um HIS/ERP. A proposta defensável é um serviço especializado de
segurança de medicação e evidência, integrável por padrão aberto a um EMR existente.

| Referência | Observação | Decisão | Racional / próximo passo |
|---|---|---|---|
| [HL7 CDS Hooks 2.0](https://cds-hooks.hl7.org/2.0/) (consultado) | discovery `GET /cds-services`, chamadas por hook (`order-select`, `order-sign`…), prefetch FHIR, cards com `info/warning/critical`, sugestões, feedback `accepted/overridden`, JWT assinado assimétrico | **EXPERIMENT** | Os indicadores dos cards do Prescripta já coincidem com os do padrão. Um adaptador `order-sign` + discovery + feedback sobre o orquestrador existente é o caminho de integração com EMR. Não afirmar conformidade sem teste. Pré-requisitos: JWT assimétrico de cliente, FHIR MedicationRequest como entrada. |
| Classes de falha dos alertas Anvisa | erros dimensionais, decimais, limite de concentração | **ADOPT** (como testes) | Implementado nesta rodada (seção 1). |
| Regra de concentração máxima por fármaco/via | necessária para eletrólitos concentrados | **DEFER** | Exige dado clínico validado por fármaco; não inventar limites. Até lá, a cobertura declara não avaliado. |
| Modelo multi-módulo hospitalar (cadastro, faturamento, estoque) | escopo de ERP | **REJECT** | Fora da finalidade; custo alto, nenhum ganho de segurança demonstrável. |
| Marketplace de parceiros de prescrição | integração por API de terceiros | **DEFER** | Sem contrato/API autorizada; nenhuma integração real será simulada. |

Benchmarks citados no prompt mestre (Medplum, OpenMRS, OHDSI ATLAS/CohortDiagnostics/DQD, OWASP
ASVS, WCAG 2.2) **não foram reconsultados nesta rodada**; decisões sobre eles ficam pendentes.
