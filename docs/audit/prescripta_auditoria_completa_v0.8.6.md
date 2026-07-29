# Auditoria completa do Prescripta — estado atual e plano para v0.8.6

**Repositório auditado:** `Soturine/Prescripta`  
**Branch:** `main`  
**Commit de referência:** `c683f2cd8ab245f04f172fc12a58319ec2c3dc70`  
**Data do commit:** 11 de julho de 2026  
**Versão correta pretendida:** `v0.8.6`  
**Versão propagada por engano no repositório:** `v8.6.0`  
**Data da auditoria:** 28 de julho de 2026  

---

## 1. Escopo, método e limitações

Esta auditoria cobriu, por inspeção estática:

- arquitetura e organização do repositório;
- backend FastAPI, domínio, serviços, repositórios e persistência SQLAlchemy;
- frontend React/TypeScript, autenticação, rotas, serviços e fluxos principais;
- regras de risco, alergia, interação, dose, psicotrópicos, política de prescrição e protocolos;
- IA assistiva, configuração de providers, minimização de dados, RAG e extração de documentos;
- relatórios, EvidenceBundles, hashes, auditoria e exportações;
- integração FHIR-like, JSON e CSV, matching, deduplicação e reconciliação;
- CI, testes, scripts de release, versionamento, dependências e governança;
- README, índice de documentação, limitações, roadmap, auditorias históricas e assets;
- experiência e lacunas sob a ótica de medicina, enfermagem, farmácia, anestesiologia,
  cardiologia, psiquiatria e psicologia;
- comparação com padrões e projetos externos: HL7 FHIR, SMART App Launch, CDS Hooks,
  OpenMRS, OpenEMR, Bahmni, HAPI FHIR, WHO Medication Without Harm, ONC SAFER,
  ANVISA, COFEN, CFP, OWASP e NIST SSDF.

### Limitação importante

Não foi possível clonar e executar o projeto localmente neste ambiente por indisponibilidade de
resolução DNS. Portanto:

- não foram reexecutados `pytest`, Vitest, Playwright, Ruff ou o build;
- não foi medida cobertura real, desempenho ou comportamento em runtime;
- os números de testes e desempenho registrados nos próprios documentos não foram validados de
  forma independente;
- os achados de código são baseados no commit conectado e nos arquivos abertos diretamente pelo
  GitHub.

Isso não invalida os problemas estruturais e lógicos encontrados, mas diferencia uma **auditoria
estática completa** de uma validação dinâmica ou clínica.

---

## 2. Veredito executivo

### Estado real do projeto

O Prescripta amadureceu de forma significativa como **produto demonstrativo de portfólio
healthtech**. Há:

- separação razoável entre frontend, backend, serviços, schemas, repositórios e integrações;
- avisos educacionais explícitos;
- boa preocupação com auditabilidade, fontes, fallback e revisão humana;
- recursos visuais e fluxos por perfil;
- testes backend em várias áreas;
- CI multiplataforma e E2E básico;
- esforço acima da média em documentação e explicação de limitações;
- vários conceitos corretos: dados ausentes não deveriam significar negativos, IA não deveria
  decidir risco, imports deveriam exigir revisão e regras deveriam ter fonte/status.

Entretanto, o projeto cresceu horizontalmente mais rápido do que o núcleo clínico foi consolidado.
O maior risco atual não é “falta de tela” ou “falta de documentação”. É a existência de **motores
paralelos, fontes de verdade duplicadas e decisões que não são agregadas em um estado clínico
canônico**.

### Classificação heurística

| Dimensão | Nota indicativa | Leitura |
|---|---:|---|
| Produto demonstrativo/portfólio | **8,0/10** | amplo, visualmente convincente e bem explicado |
| Arquitetura de aplicação | **6,2/10** | modularidade parcial, mas serviços grandes e transações fragmentadas |
| Qualidade e manutenibilidade | **5,8/10** | boa intenção, porém duplicações, God Objects e contratos genéricos |
| Testes automatizados | **5,5/10** | backend razoável; frontend, segurança e semântica clínica insuficientes |
| Segurança da aplicação demo | **5,0/10** | JWT/RBAC funcionam, mas faltam controles importantes |
| Interoperabilidade | **3,5/10** | adapters e reconciliação demonstrativos, não FHIR conformante |
| Auditabilidade histórica | **4,0/10** | muitos eventos, mas snapshots não são imutáveis e commits são fragmentados |
| Segurança clínica | **3,0/10** | existem boas proteções locais, mas falta decisão agregada e abstention forte |
| Prontidão operacional | **2,5/10** | SQLite, `create_all`, auto-seed, sem deploy/backup/observabilidade |
| Prontidão regulatória/clínica real | **1,5/10** | sem validação clínica, QMS, gestão formal de risco ou evidência de desempenho |

Essas notas não são certificação. Servem apenas para priorização.

### Conclusão principal

**O Prescripta deve continuar sendo apresentado como protótipo educacional. Ele não está pronto
para dados reais, uso assistencial ou tomada de decisão clínica.**

Antes de adicionar novas especialidades ou medicamentos, a prioridade deve ser:

1. corrigir o versionamento para `v0.8.6`;
2. unificar a decisão clínica;
3. tornar unidade/dose semanticamente segura;
4. impedir falsa segurança quando não há cobertura;
5. tornar evidência e auditoria imutáveis;
6. implementar autorização por objeto/contexto;
7. criar transações atômicas;
8. reduzir duplicações de modelo, serviço e documentação;
9. fortalecer testes clínicos, de segurança e de autorização.

---

## 3. Achados impeditivos — P0

## P0-01 — Os motores clínicos não alimentam uma decisão canônica única

### Evidência

A rota principal executa o `RiskEngine`, persiste seu resultado e só depois calcula:

- Dose Intelligence;
- segurança psicotrópica;
- política do prescritor;
- counseling;
- contexto funcional;
- RAG.

Os resultados posteriores são anexados à resposta, mas não atualizam de forma determinística:

- `status`;
- `risk_level`;
- `human_review_required`;
- `recommendation`.

### Consequência

É possível uma resposta conter simultaneamente:

- decisão principal “liberada”;
- sinal psicotrópico `CRITICAL`;
- policy `blocked_by_policy`;
- Dose Intelligence acima do máximo;
- necessidade de especialista ou segunda revisão.

A interface mostra primeiro a recomendação principal e depois cartões separados. Isso permite
contradição cognitiva: o usuário vê um “verde” geral e, abaixo, um bloqueio crítico.

### Correção obrigatória

Criar um `ClinicalDecisionOrchestrator` que:

1. coleta todos os módulos;
2. transforma cada achado em um contrato comum;
3. agrega severidade segundo regra explícita;
4. decide cobertura, abstention, bloqueio, revisão e liberação;
5. persiste somente o envelope final;
6. produz uma recomendação coerente e única.

Contrato sugerido:

```text
ClinicalDecisionEnvelope
├── decision_status
│   ├── not_evaluated
│   ├── insufficient_data
│   ├── insufficient_coverage
│   ├── review_required
│   ├── blocked
│   └── evaluated_no_issue
├── highest_severity
├── coverage
├── findings[]
├── required_actions[]
├── override_policy
├── source_snapshot
├── rule_versions
└── human_review_required
```

Evitar a palavra `released` para um sistema educacional. “Nenhum problema foi encontrado dentro da
cobertura disponível” é muito mais seguro.

---

## P0-02 — Semântica de dose incompatível com as unidades anunciadas

### Evidência

O domínio principal recebe exclusivamente:

- `dose_mg`;
- `frequency_per_day`;
- total diário em mg.

Ao mesmo tempo, as regras aceitam:

- `mcg`;
- `mg/kg`;
- `mg/kg/dia`;
- `mcg/kg`;
- `mg/m²`;
- `mcg/kg/min`;
- `mg/kg/h`.

O Dose Intelligence compara o valor numérico de `dose_mg × frequência` com limites expressos em
outras unidades sem uma camada explícita de conversão, dimensão, concentração, taxa ou tempo.

### Consequências

Exemplos de erros possíveis:

- comparar mg com mcg;
- comparar dose diária com dose por minuto;
- multiplicar frequência em uma infusão contínua;
- tratar `mcg/kg/min` como se fosse mg por administração;
- ignorar concentração `mg/mL`;
- ignorar velocidade, diluição e volume;
- aplicar máximo diário a uma regra por procedimento.

### Correção obrigatória

Substituir `dose_mg` por uma estrutura dimensional:

```text
MedicationDose
├── amount
├── amount_unit         # mg, mcg, g, mL, UI etc.
├── concentration       # opcional: mg/mL
├── administration_kind # bolus, intermittent, continuous, PRN
├── rate                # amount/time ou volume/time
├── frequency
├── interval
├── duration
├── route
├── site
└── procedure_context
```

Usar uma biblioteca ou camada interna de quantidades com conversão explícita e testes de
propriedade. Uma regra só pode ser comparada a uma prescrição quando as dimensões forem
compatíveis.

---

## P0-03 — Cálculos de peso ideal/massa magra usam sexo inexistente e assumem feminino

### Evidência

O Dose Intelligence lê `patient.sex`, mas o modelo, domínio e schema de paciente não oferecem esse
campo. Quando ausente, o código usa `unspecified`; a fórmula cai no ramo feminino para peso ideal e
massa magra.

### Consequência

O sistema produz número aparentemente preciso com um dado não coletado. É uma falha de segurança
por **imputação silenciosa**.

### Correção obrigatória

- nunca assumir sexo/fator corporal ausente;
- retornar `insufficient_data`;
- registrar exatamente qual variável falta;
- separar sexo biológico necessário à fórmula, identidade de gênero e uso clínico;
- documentar a fórmula, população, limitações e fonte;
- testar masculino, feminino, não informado, extremos antropométricos e impossibilidades.

---

## P0-04 — Ausência de cobertura pode produzir falsa segurança

### Evidência

Há fluxos em que:

- nenhum contexto clínico produz poucos ou nenhum alerta de incompletude;
- falta de regra específica não impede recomendação tranquilizadora;
- o CDS externo cria medicamento com máximo diário enorme por padrão;
- paciente externo sem peso recebe 70 kg;
- `missing_data_mode` pode permitir continuidade;
- interaction checker possui apenas um conjunto pequeno de pares demonstrativos.

### Consequência

“Nenhum alerta” pode significar:

1. o caso foi avaliado e está adequado;
2. a regra não existe;
3. a fonte não é válida;
4. o contexto está ausente;
5. o medicamento foi recebido com limites fornecidos pelo próprio cliente;
6. o algoritmo não reconheceu o termo.

Esses estados não podem compartilhar a mesma aparência.

### Correção obrigatória

Adicionar `coverage_status` obrigatório:

- `covered`;
- `partially_covered`;
- `not_covered`;
- `unknown_medication`;
- `rule_pending_review`;
- `source_expired`;
- `required_context_missing`.

Proibir resultado tranquilizador quando `coverage_status != covered`.

---

## P0-05 — O endpoint “CDS” confia em regras e limites fornecidos pelo cliente

### Evidência

O endpoint `/cds/prescription-check` constrói `Patient` e `Medication` diretamente do payload:

- peso padrão de 70 kg;
- dose padrão de 1 mg;
- máximo diário padrão de 999999 mg;
- rota padrão oral;
- contraindicações, cautelas e limites vindos do solicitante;
- fonte padrão `external_demo`.

### Consequência

O endpoint não é um serviço CDS confiável; é um executor de regra fornecida por quem chama. Um
cliente pode omitir cautelas e receber um resultado artificialmente favorável.

### Correção obrigatória

- receber apenas contexto clínico e uma referência canônica ao medicamento/ordem;
- resolver conhecimento e regras no servidor;
- rejeitar medicamento desconhecido;
- não imputar peso;
- não inventar máximo;
- implementar contrato CDS Hooks real ou renomear para
  `/demo/evaluate-client-supplied-rule`;
- registrar versão da regra, hook, contexto e decisão;
- usar cards, suggestions, links e override reasons conforme CDS Hooks.

---

## P0-06 — Relatórios históricos podem mudar depois da decisão

### Evidência

O `EvidenceBundle` de uma checagem é reconstruído consultando o paciente e o medicamento atuais.
O registro gerado armazena hashes e metadados, mas não conserva necessariamente:

- o bundle completo imutável;
- o arquivo PDF original;
- o snapshot das regras;
- a fonte exatamente como estava;
- a versão de todos os fatos clínicos.

### Consequência

Se o paciente, medicamento, fonte ou regra forem atualizados, o mesmo `audit_id` pode gerar um
bundle diferente. Isso quebra:

- reprodutibilidade;
- cadeia de custódia;
- confiança no hash;
- auditoria forense;
- comparação de versões;
- validade documental.

### Correção obrigatória

No mesmo commit transacional da decisão, persistir:

- input normalizado;
- snapshot de paciente mínimo usado;
- snapshot de medicamento;
- regras e versões;
- findings;
- decisão agregada;
- fontes;
- hash canônico;
- ator;
- timestamp;
- correlação/idempotency key.

O PDF/JSON emitido deve ficar em armazenamento imutável ou ser regenerável **somente** a partir
desse snapshot, nunca do cadastro corrente.

---

## P0-07 — Autorização é apenas por papel global, sem autorização por objeto

### Evidência

As rotas validam perfis globais (`admin`, `medico`, `enfermagem`, `auditor`), mas não demonstram:

- instituição/tenant;
- unidade;
- equipe assistencial;
- vínculo com paciente;
- finalidade do acesso;
- consentimento;
- escopo de especialidade;
- break-glass;
- redaction por campo.

IDs sequenciais de pacientes, documentos, relatórios, imports e auditorias são recebidos diretamente.

### Consequência

Em uma instância com dados reais, um profissional autenticado poderia potencialmente consultar
objetos de qualquer paciente acessível ao sistema. Isso é uma forma de risco BOLA/IDOR e viola o
princípio de mínimo acesso.

### Correção obrigatória

Implementar:

- `Organization`, `Facility`, `CareTeam`, `PractitionerRole`;
- associação usuário–organização–papel;
- policies por objeto;
- escopo do paciente/encounter;
- propósito de uso;
- break-glass com motivo, prazo e alerta;
- filtros no repositório, não só na rota;
- DTOs por perfil e minimização de propriedades;
- testes negativos para todos os endpoints com IDs.

---

## P0-08 — Configuração demo pode ser iniciada silenciosamente fora de ambiente local

### Evidência

Defaults incluem:

- segredo JWT conhecido;
- SQLite local;
- `auto_seed=true`;
- credenciais demo documentadas;
- CORS local amplo;
- criação automática de tabelas.

### Consequência

Uma implantação descuidada pode expor:

- usuários e senhas conhecidas;
- tokens assinados com segredo público;
- dados seed;
- estrutura sem migrações;
- comportamento de demo em ambiente de teste ou produção.

### Correção obrigatória

No startup:

```text
se environment != development/demo:
    falhar se secret default
    falhar se auto_seed
    falhar se SQLite
    falhar se CORS wildcard ou origem insegura
    falhar se credenciais demo existirem
    falhar se encryption key ausente
```

Usar configurações tipadas e validação cruzada.

---

## P0-09 — Ausência de transação clínica atômica

### Evidência

Repositórios e serviços fazem `commit()` internamente. Uma checagem pode executar:

1. gravação de `PrescriptionAudit`;
2. gravação de evento principal;
3. gravação de um evento por alerta;
4. atualização de counseling;
5. atualização de histórico;
6. cálculos posteriores;
7. atualização do audit;
8. novos eventos.

Protocolos e reports seguem padrão semelhante.

### Consequência

Uma falha intermediária deixa:

- decisão sem módulos posteriores;
- protocolo sem evento;
- relatório sem auditoria;
- auditoria parcial;
- múltiplos eventos fora de sincronia;
- retries duplicados.

### Correção obrigatória

- retirar `commit()` dos repositórios;
- introduzir `UnitOfWork`;
- uma transação por caso de uso;
- rollback integral;
- idempotency key;
- outbox para eventos assíncronos;
- constraints para impedir duplicação;
- testes de falha em cada etapa.

---

## P0-10 — O sistema ainda não possui validação clínica formal

### Situação

Os avisos educacionais estão corretos, mas o volume de funcionalidades, especialidades, protocolos
e regras pode transmitir uma percepção de cobertura maior do que a evidência permite.

### Para qualquer uso real seriam necessários

- finalidade de uso formal;
- classificação regulatória;
- gestão de risco;
- equipe clínica responsável;
- processo de curadoria;
- validação analítica;
- validação clínica;
- avaliação de usabilidade/human factors;
- vigilância pós-implantação;
- controle de mudança;
- QMS;
- segurança e privacidade;
- estudos de sensibilidade, especificidade, PPV/NPV e alert burden;
- governança institucional.

A documentação não substitui esses processos.

---

## 4. Achados de alta prioridade — P1

| ID | Achado | Impacto | Correção |
|---|---|---|---|
| P1-01 | Versão `v8.6.0` propagada no backend, frontend, README, docs, assets e scripts | release incorreta e metadados divergentes | corrigir tudo para `v0.8.6` e criar gate sem versão hardcoded |
| P1-02 | `policy_version` e versão da aplicação estão misturadas | policy clínica muda ao atualizar app | versionar policy de forma independente |
| P1-03 | `RiskEngine` com aproximadamente 900 linhas | baixa testabilidade, duplicação e efeitos colaterais | dividir em regras pequenas e registry |
| P1-04 | `EmergencyProtocolService` com mais de 600 linhas e `ruff: noqa: E501` | biblioteca, persistência, IA e relatório acoplados | separar definição, execução, persistência e apresentação |
| P1-05 | `api.ts` frontend com mais de 500 linhas | acoplamento de todos os domínios | clientes por módulo e camada de erros |
| P1-06 | Três normalizadores com semânticas diferentes | uma regra casa em um módulo e falha em outro | serviço único de terminologia/matching |
| P1-07 | `MedicationModel` monolítico duplica catálogo normalizado | divergência entre princípio ativo, produto e regras | migrar para entidades versionadas |
| P1-08 | Models/serviços mortos | confusão e dívida | remover ou integrar explicitamente |
| P1-09 | Listagens sem paginação | degradação e excesso de exposição | paginação server-side obrigatória |
| P1-10 | N+1 no catálogo e respostas | desempenho inconsistente | eager loading/batch queries |
| P1-11 | Busca por substring em alergia/interação | falsos positivos/negativos | códigos canônicos e matching explícito |
| P1-12 | `Patient.age` e `birth_date` coexistem sem invariantes | idade divergente | armazenar data; calcular idade na data clínica |
| P1-13 | Condições e medicamentos são listas de strings | sem status, data, fonte e certeza | recursos clínicos estruturados |
| P1-14 | Admin tratado como prescritor em algumas policies | mistura administração e ato clínico | separar impersonation/test mode de papel clínico |
| P1-15 | Não há workflow de override/segunda revisão | policy declarada, não operacional | entidade `DecisionOverride` e coassinatura |
| P1-16 | `base_url` de IA livre | SSRF e acesso a rede interna | validação URL, allowlist e egress control |
| P1-17 | circuit breaker e credenciais só em memória | comportamento diferente com workers | storage compartilhado e secrets manager |
| P1-18 | payload da explicação clínica vem do cliente | adulteração e inconsistência | explicar por `audit_id` canônico |
| P1-19 | minimização de IA incompleta | possível envio de PII/PHI | allowlist de campos, DLP e teste de privacidade |
| P1-20 | RAG faz varredura de Markdown por requisição | baixa precisão e escalabilidade | índice versionado, chunks, metadados e validação |
| P1-21 | hash de documento usa `repr(dict)` | canonicidade frágil | JSON canônico e hash versionado |
| P1-22 | auditoria inclui nomes/e-mails e details livres | excesso de dados e difícil redaction | schema de evento, tokenização e políticas de retenção |
| P1-23 | múltiplas tabelas/trilhas de auditoria | busca e consistência difíceis | event model canônico + projeções |
| P1-24 | filtro de JSON por cast para texto | lento e semanticamente impreciso | colunas indexadas/PostgreSQL JSONB |
| P1-25 | relatório de auditoria limita 500 sem evidenciar truncamento | relatório incompleto | paginação/streaming e manifesto |
| P1-26 | token JWT em localStorage | roubo por XSS | cookie HttpOnly/BFF ou OIDC seguro |
| P1-27 | login sem rate limit/lockout/MFA | brute force e tomada de conta | rate limiting, lockout, MFA e audit |
| P1-28 | `/health` expõe ambiente/provider | disclosure desnecessário | readiness interno e health público mínimo |
| P1-29 | ausência de migrations reais | evolução insegura do schema | Alembic e testes upgrade/downgrade |
| P1-30 | ausência de PostgreSQL em CI | comportamento JSON/constraints não testado | service container Postgres |
| P1-31 | dependências de teste no runtime | imagem maior e superfície de ataque | `requirements`/groups separados |
| P1-32 | `npm run lint` não faz lint | falsa indicação de qualidade | ESLint + React hooks + accessibility |
| P1-33 | ausência de SAST/SCA/secret scan/SBOM | supply-chain sem gate | CodeQL, pip-audit, npm audit/OSV, gitleaks, CycloneDX |
| P1-34 | workflow permite release direto na `main` | sem revisão independente | branch protection, PR e CODEOWNERS |
| P1-35 | Actions por tags mutáveis | risco de supply chain | pin por SHA |
| P1-36 | sem `SECURITY.md`, `CODEOWNERS`, Dependabot/Renovate | vulnerabilidades sem processo | adicionar governança |
| P1-37 | docs correntes misturam release notes | conteúdo fica datado | docs canônicos version-neutral |
| P1-38 | `docs/audience` e `docs/audiences` coexistem | duplicação e links ambíguos | consolidar um diretório |
| P1-39 | screenshots e GIFs versionados em grande volume | repositório pesado e duplicado | GitHub Releases/LFS ou somente conjunto atual |
| P1-40 | testes E2E focam presença de tela | não detectam falha clínica | cenários de decisão e autorização negativa |

---

## 5. Código morto e duplicações confirmadas

## 5.1 Código morto confirmado por busca de referências

Os seguintes símbolos apareceram apenas em sua própria definição no índice conectado:

- `MedicationExposurePlanModel`;
- `MedicationMechanismProfileModel`;
- `ExternalPatientIdentityModel`;
- `MedicationExposureService`;
- `MedicationExposurePlan`.

### Problema adicional

Alguns desses elementos duplicam conceitos existentes no `MedicationModel` e em objetos de
resposta. Mantê-los “para o futuro” aumenta o risco de alguém começar a escrever em uma fonte e ler
de outra.

### Decisão recomendada

Para cada elemento:

1. existe caso de uso e rota planejados para a próxima versão?
2. há contrato, owner e teste?
3. é parte da arquitetura alvo?

Se a resposta for não, remover. Se sim, criar issue e integrar de ponta a ponta antes de mantê-lo.

## 5.2 Duplicações arquiteturais

### Medicamento

Hoje coexistem:

- `MedicationModel` legado/monolítico;
- `ActiveIngredientModel`;
- `DrugProductModel`;
- regras de dose embutidas;
- policy embutida;
- mecanismo/PK embutidos;
- counseling embutido;
- aliases em mais de um local.

Arquitetura alvo:

```text
ActiveIngredient
DrugProduct
MedicationKnowledgeVersion
DoseRuleVersion
InteractionRuleVersion
ContraindicationRuleVersion
PrescribingPolicyVersion
CounselingContentVersion
SourceDocumentVersion
```

Cada regra deve apontar para fonte, jurisdição, versão, vigência, status de revisão e approvers.

### Auditoria

Há registros especializados e eventos genéricos. Consolidar em:

- evento imutável canônico;
- snapshots de decisão;
- projeções para dashboards;
- anexos/artefatos por hash.

### Normalização

Consolidar:

- remoção de acentos/case;
- aliases;
- DCB;
- código local;
- terminologia externa;
- matching exato;
- fuzzy match apenas como sugestão;
- provenance da resolução.

### Documentação

Consolidar:

- um README estável;
- um `docs/README.md` realmente completo;
- uma área `docs/history/` para auditorias e planos antigos;
- release notes em GitHub Releases/`CHANGELOG.md`;
- docs correntes sem nomes de versão;
- assets atuais em diretório não versionado ou em release.

---

## 6. Auditoria detalhada das regras clínicas

## 6.1 Regra fundamental: “ausente” não é “não”

O README declara esse princípio, mas ele não é aplicado de modo uniforme.

Exemplos:

- listas vazias podem significar “nenhum item” ou “não coletado”;
- booleanos default `False` confundem negativo com desconhecido;
- `pregnancy_or_lactation` é opcional, mas outros fatores não têm status;
- CDS usa defaults;
- contexto ausente pode continuar;
- source refs ausentes apenas geram detalhe local.

### Modelo recomendado

Todo fato clínico relevante deve ter:

```text
value
status: known_present | known_absent | unknown | not_asked | declined | unavailable
effective_time
recorded_time
source
recorder
verification_status
confidence
```

---

## 6.2 Alergias

### Limitações atuais

- strings livres;
- comparação por substring;
- sem substância/produto/classe estruturada;
- sem tipo de reação;
- sem severidade;
- sem certeza;
- sem status ativo/inativo;
- sem data;
- sem fonte;
- sem diferenciação entre alergia, intolerância e efeito adverso;
- sem cross-reactivity governada;
- sem “entered in error”.

### Recomendação

Adotar estrutura compatível com `AllergyIntolerance`, usando códigos e vínculo ao princípio ativo.
Alergia sem reação documentada deve continuar relevante, mas aparecer como incompleta, não como
prova de reação específica.

---

## 6.3 Interações

### Limitações atuais

- pequena tabela demonstrativa;
- matching textual;
- sem mecanismo;
- sem contexto de dose;
- sem intervalo;
- sem via;
- sem relevância clínica;
- sem ação recomendada;
- sem fonte/versionamento em cada regra;
- sem contraindicação absoluta versus monitoramento;
- sem ajuste por idade, rim, fígado, eletrólitos ou ECG.

### Alert fatigue

A literatura mostra taxas muito altas de override de alertas DDI. O Prescripta não deve crescer
simplesmente adicionando milhares de alertas. É necessário:

- tiering;
- supressão contextual;
- alertas acionáveis;
- motivo de override;
- monitoramento de aceitação;
- revisão periódica;
- métricas por regra;
- desativação de regras de baixo valor.

---

## 6.4 Dose

### Lacunas gerais

- unidade e dimensão;
- forma farmacêutica;
- concentração;
- volume;
- taxa;
- intervalos;
- PRN;
- dose de ataque/manutenção;
- teto por administração;
- teto por dia;
- teto por curso;
- teto por procedimento;
- washout;
- titulação;
- taper;
- função renal;
- função hepática;
- idade gestacional;
- idade pós-natal;
- obesidade extrema;
- diálise;
- indicação;
- interação;
- farmacogenômica;
- laboratório atual e validade temporal.

### Recomendação

Cada regra precisa declarar:

```text
population
indication
route
form
administration_kind
dose_dimension
calculation_basis
required_inputs
exclusion_criteria
usual_range
hard_limits
monitoring
source_versions
effective_period
review_status
approved_by
```

Uma regra pendente pode ser exibida como exemplo, mas não deve produzir resultado verde.

---

## 6.5 Psicotrópicos

O módulo cobre vários riscos relevantes como sinais demonstrativos, mas ainda é uma coleção
hardcoded e paralela.

### Requisitos ausentes ou incompletos

- fase do transtorno;
- tentativa/suicidalidade atual;
- episódio maníaco/psicótico;
- uso de álcool e substâncias com status temporal;
- washout e cross-taper;
- descontinuação/taper;
- adesão;
- uso de depot/LAI;
- ECG/QTc;
- eletrólitos;
- função renal/tiroide para lítio;
- hemograma/ANC para clozapina;
- gravidez e contracepção para valproato;
- peso, cintura, glicemia e lipídios para antipsicóticos;
- níveis séricos;
- efeitos adversos observados;
- data/validade dos exames.

### Regra de produto

“Sinal psicotrópico” não deve virar diagnóstico. O sistema deve mostrar:

- o que foi observado;
- o que está faltando;
- qual fonte disparou;
- qual ação humana é esperada;
- se é bloqueio, monitoramento ou encaminhamento.

---

## 6.6 Policy do prescritor

O projeto fez corretamente a distinção conceitual entre:

- autorização de sistema;
- norma legal/regulatória;
- policy institucional;
- recomendação clínica;
- regra demo.

Mas a execução não está completa.

### O que falta

- instituição;
- vigência;
- local/unidade;
- profissão e conselho;
- especialidade verificada;
- escopo do protocolo;
- paciente/contexto;
- medicamento/forma;
- tipo de receituário;
- coassinatura;
- override;
- justificativa;
- approver;
- trilha de mudança;
- conflito entre policies;
- precedência.

### Regra de precedência sugerida

1. indisponibilidade de dados críticos → abstention;
2. hard block legal/regulatório validado;
3. hard block institucional vigente;
4. requisito de segunda revisão;
5. safety clinical block;
6. warning/recomendação;
7. informational.

Policy demo nunca deve se declarar bloqueio legal.

---

## 6.7 Alternativas medicamentosas

O módulo atual pode sugerir itens relacionados, mas não dispõe de contexto suficiente para uma
“alternativa clínica”.

Uma alternativa exige, no mínimo:

- mesma indicação;
- objetivo terapêutico;
- contraindicações;
- alergias;
- interações;
- função renal/hepática;
- gravidez;
- idade;
- formulação/via;
- disponibilidade/formulário;
- custo/acesso;
- guideline;
- equivalência;
- necessidade de washout/cross-taper.

Até lá, usar o rótulo **“itens relacionados para revisão”**, não “alternativas”.

---

## 7. Perspectiva dos profissionais de saúde

## 7.1 Médico generalista/clínico

### O que já ajuda

- visão de paciente;
- dose, via e duração;
- alertas;
- histórico;
- documentos;
- fontes;
- relatório;
- auditoria.

### O que falta

- encontro/consulta;
- diagnóstico/indicação codificada;
- problema ativo versus histórico;
- exames e sinais vitais com data;
- plano terapêutico;
- objetivos;
- follow-up;
- prescrição completa;
- formulary;
- monitoramento;
- assinatura/coassinatura;
- contraindicação absoluta versus relativa;
- reconciliação na transição de cuidado;
- possibilidade de marcar alerta como aceito, não aplicável ou superado.

---

## 7.2 Enfermagem

### Correção conceitual importante

A aplicação não deve presumir que enfermagem “não prescreve”. A Resolução COFEN nº 801/2026
estabelece prescrição pelo enfermeiro no contexto de consulta de enfermagem, fundamentada em
protocolos/rotinas aprovados e programas de saúde pública, com requisitos formais e
rastreabilidade.

### Fluxos necessários

- consulta de enfermagem;
- protocolo institucional vigente;
- instituição/CNPJ;
- identificação e registro COREN;
- DCB;
- concentração, apresentação, via e posologia;
- assinatura eletrônica;
- registro no prontuário;
- Processo de Enfermagem;
- adverse event notification;
- escopo por protocolo, não por papel genérico.

### Para administração segura

- medicamento, paciente, dose, via e horário corretos;
- razão/indicação;
- documentação;
- resposta;
- educação;
- direito de recusa;
- dupla checagem de high-alert;
- hold parameters;
- infusão e bomba;
- concentração/diluição;
- lote/validade quando necessário;
- omissão/atraso e motivo;
- escalonamento.

O Prescripta ainda é centrado em prescrição/checagem, não em eMAR/MAR.

---

## 7.3 Farmacêutico — papel ausente e essencial

O projeto menciona farmacêutico nos avisos, mas não possui papel de usuário próprio.

### Deve existir

- verificação farmacêutica;
- reconciliação;
- história medicamentosa;
- dispensação;
- formulary;
- substituição;
- intervenção farmacêutica;
- stewardship;
- dose renal/hepática;
- compatibilidade;
- duplicidade terapêutica;
- alergia/intolerância;
- monitoramento;
- fila de pendências;
- aceitação/rejeição pelo prescritor;
- métricas de intervenção.

Esse é um dos maiores vazios de produto.

---

## 7.4 Anestesiologista

A anestesia é uma das áreas em que as unidades anunciadas pelo projeto mais exigem segurança
dimensional.

### Necessidades

- peso real, ideal, ajustado e massa magra sem imputação;
- ASA, via aérea e procedimento;
- idade, fragilidade, gravidez;
- função cardíaca, renal e hepática;
- bolus versus infusão;
- concentração;
- volume;
- taxa;
- dose cumulativa;
- anestésico local total e combinação;
- intervalo;
- monitorização;
- bloqueadores neuromusculares/reversão;
- interações;
- alergia;
- disponibilidade de resgate;
- timeline intraoperatória;
- sinais vitais.

Uma regra de `mcg/kg/min` não pode reutilizar um formulário de `dose_mg × vezes/dia`.

---

## 7.5 Cardiologista

### Contexto mínimo

- pressão e frequência;
- ritmo;
- ECG;
- QT/QTc e fórmula utilizada;
- potássio, magnésio e cálcio;
- creatinina/eGFR/CrCl;
- fração de ejeção;
- insuficiência cardíaca;
- anticoagulação/antiagregação;
- sangramento;
- função hepática;
- interações;
- bradicardia;
- gravidez;
- adesão.

Scores como CHA₂DS₂-VASc ou HAS-BLED só devem entrar com:

- definição formal;
- população;
- versão;
- fonte;
- inputs obrigatórios;
- testes;
- limitação;
- validação.

---

## 7.6 Psiquiatra

### Contexto necessário

- diagnóstico e fase;
- sintomas-alvo;
- risco de suicídio;
- mania/psicose;
- uso de substâncias;
- tentativa anterior;
- adesão;
- resposta prévia;
- cross-taper/washout;
- síndrome de descontinuação;
- gravidez/reprodução;
- peso/metabólico;
- ECG;
- labs;
- níveis séricos;
- clozapina/ANC;
- lítio/renal/tiroide;
- valproato;
- efeitos adversos;
- consentimento e capacidade.

O módulo de sinais é útil como demonstração, mas não substitui um workflow de monitoramento.

---

## 7.7 Psicólogo

O psicólogo não deve ser inserido como um “prescritor alternativo”. O valor do Prescripta para
psicologia seria:

- observações clinicamente necessárias;
- evolução sintética;
- encaminhamentos;
- fatores de adesão;
- risco e escalonamento;
- consentimento;
- plano interdisciplinar;
- informação mínima relevante para equipe.

### Requisito de sigilo

É necessário separar:

- prontuário multiprofissional: somente informação necessária ao cuidado;
- prontuário psicológico;
- materiais exclusivos/privativos;
- avaliação/testes;
- níveis de acesso;
- exportação e entrega ao usuário;
- retenção/descarte;
- responsável pela guarda.

Hoje o modelo de paciente e documentos não oferece segregação suficiente.

---

## 7.8 Outros perfis que deveriam entrar no roadmap

- pediatria/neonatologia;
- obstetrícia;
- geriatria;
- nefrologia;
- hepatologia;
- infectologia e stewardship;
- oncologia;
- UTI;
- emergência;
- odontologia;
- farmácia clínica;
- qualidade/segurança do paciente;
- farmacovigilância;
- gestão de dados/terminologia;
- responsável técnico;
- DPO/encarregado;
- engenharia clínica/TI.

---

## 8. Interoperabilidade — comparação com FHIR e CDS Hooks

## 8.1 Problema do modelo atual

O Prescripta concentra muitos conceitos em `MedicationModel` e em listas de strings.

FHIR separa, por finalidade:

- `MedicationRequest`: ordem/pedido;
- `MedicationDispense`: fornecimento;
- `MedicationAdministration`: administração real;
- `MedicationStatement`: relato/uso;
- `Medication`: produto/substância;
- `MedicationKnowledge`: conhecimento;
- `AllergyIntolerance`;
- `Condition`;
- `Observation`;
- `DiagnosticReport`;
- `DocumentReference`;
- `Provenance`;
- `AuditEvent`;
- `PlanDefinition`;
- `GuidanceResponse`.

Essa separação reduz ambiguidade e permite lifecycle/status próprios.

## 8.2 O que “FHIR-like” deve significar hoje

O projeto atual:

- aceita um subconjunto de payload;
- transforma alguns campos;
- persiste source/mapped payload;
- cria lote;
- permite revisão;
- aplica itens selecionados.

Isso é uma **importação demonstrativa com reconciliação**, não uma implementação FHIR.

### Renomear claramente

- “Importar payload FHIR demonstrativo”;
- “Compatibilidade parcial, sem validação de perfil”;
- “Não é servidor FHIR”;
- “Não suporta transação FHIR”.

## 8.3 Caminho de maturidade

1. escolher FHIR R4 para compatibilidade prática;
2. escrever Implementation Guide do Prescripta;
3. criar CapabilityStatement;
4. definir perfis;
5. validar com official validator/HAPI;
6. terminologia versionada;
7. OperationOutcome;
8. idempotência;
9. versionId/lastUpdated;
10. Provenance;
11. AuditEvent;
12. conditional create/update;
13. transaction Bundle;
14. SMART App Launch/OAuth scopes;
15. testes de conformidade.

## 8.4 CDS Hooks

A rota atual não implementa o protocolo.

Implementação real deve incluir:

- discovery;
- hook definido;
- `hookInstance`;
- FHIR server;
- context;
- prefetch;
- cards;
- indicator;
- source;
- suggestions;
- links;
- override reasons;
- feedback;
- autenticação;
- latência controlada.

---

## 9. IA e RAG

## 9.1 Pontos positivos

- provider opcional;
- fallback;
- chave no backend;
- structured output;
- source locking em alguns fluxos;
- IA não deveria alterar decisão;
- auditoria de provider/model;
- extrações pendentes de revisão.

## 9.2 Problemas

### Payload adulterável

A explicação recebe o resultado clínico montado no frontend. O servidor deveria receber somente
`audit_id` e carregar o snapshot canônico.

### Minimização incompleta

Remover nome e data de nascimento não é suficiente. E-mail, telefone, nome da mãe, notas e outros
campos podem continuar no objeto.

### SSRF

`base_url` livre é usado em chamadas HTTP. Validar:

- `https` obrigatório fora de local;
- hostname;
- IP resolvido;
- bloquear loopback, link-local, RFC1918, metadata cloud e DNS rebinding;
- allowlist;
- redirects;
- portas;
- tamanho/timeout;
- egress proxy.

### RAG rudimentar

O retriever:

- lê todos os Markdown;
- tokeniza por palavras;
- calcula interseção;
- usa excerpt simples;
- não prova integridade;
- não filtra efetividade/expiração;
- não separa contexto por pergunta;
- não mede recall/precision.

É melhor chamá-lo de “busca lexical em base demo” até implementar:

- indexação;
- chunking;
- metadata filters;
- embeddings opcionais;
- reranking;
- deduplicação;
- source/version lock;
- validade;
- avaliações;
- citações em nível de trecho;
- proteção contra prompt injection documental.

### Governança de IA

Adicionar:

- registro de prompt;
- dataset de avaliação;
- testes de groundedness;
- red teaming;
- logs sem PHI;
- consentimento/base legal;
- retention;
- custo/rate limit;
- kill switch;
- política por finalidade;
- fallback sem linguagem enganosa.

---

## 10. Segurança e LGPD

## 10.1 Modelo de ameaça prioritário

Ativos:

- dados clínicos;
- credenciais;
- tokens;
- chaves de IA;
- documentos;
- relatórios;
- políticas;
- regras;
- auditoria.

Ameaças:

- acesso a paciente por ID;
- elevação de privilégio;
- XSS/token theft;
- SSRF;
- import malicioso;
- prompt injection;
- mass assignment;
- exposição excessiva;
- relatório não anonimizado;
- secrets no log;
- seed em produção;
- adulteração de regra;
- supply chain;
- perda do banco;
- insider abuse.

## 10.2 Controles faltantes

- threat model;
- data flow diagram;
- classificação de dados;
- DPIA/RIPD;
- política de retenção;
- direito do titular;
- segregação;
- encryption at rest;
- KMS;
- backup criptografado;
- restore test;
- incident response;
- breach process;
- access review;
- audit review;
- vulnerability disclosure;
- dependency management;
- pentest;
- CSP;
- CSRF se cookies;
- secure headers;
- rate limit;
- request size;
- malware scanning de uploads futuros;
- session management;
- MFA;
- break-glass.

## 10.3 “Anonimizado” versus pseudonimizado

`Paciente #P-00001` continua vinculável ao registro local. Isso é pseudonimização/redução de
identificação, não anonimização robusta. Renomear modo para:

- `pseudonymized`;
- `deidentified_demo`;
- `internal_minimized`.

Uma exportação externa exige avaliação de reidentificação e remoção de datas, texto livre e
identificadores indiretos.

---

## 11. Testes e qualidade

## 11.1 O que existe

O repositório contém testes para:

- autenticação;
- API de prescrição;
- risk engine;
- alergia;
- interação;
- dose;
- IA;
- interoperabilidade;
- catálogo;
- protocolos;
- relatórios;
- hardening;
- prontidão;
- fluxos clínicos de versões anteriores;
- Vitest básico;
- Playwright de fluxos principais.

## 11.2 Lacunas críticas

### Testes clínicos

- agregação de motores;
- CRITICAL psicotrópico muda decisão;
- hard block muda decisão;
- unidades incompatíveis recusadas;
- mcg↔mg;
- infusão;
- dose por procedimento;
- sexo ausente;
- idade calculada;
- ausência de regra;
- fonte expirada;
- policy conflict;
- override;
- repetibilidade do snapshot;
- regras de borda;
- property-based testing;
- mutation testing.

### Segurança

- BOLA em cada recurso;
- BFLA;
- propriedade excessiva;
- JWT inválido/expirado/revogado;
- brute force;
- SSRF;
- XSS;
- prompt injection;
- import oversized;
- CSV injection;
- path traversal;
- secrets;
- CORS;
- CSRF;
- mass assignment;
- redaction.

### Banco

- PostgreSQL;
- migrations;
- concorrência;
- rollback;
- deadlock;
- constraint;
- idempotência;
- timezone;
- JSONB;
- backup/restore.

### Frontend

- formulários;
- validação cruzada;
- erros;
- foco/teclado;
- leitor de tela;
- contrastes;
- live regions;
- estados contraditórios;
- sessão;
- downloads;
- permissões negativas;
- múltiplos browsers.

## 11.3 Gates mínimos recomendados

```text
Backend:
- Ruff
- mypy/pyright
- pytest
- coverage >= threshold por módulo crítico
- hypothesis
- mutation score para rules
- Bandit/Semgrep
- pip-audit/OSV
- PostgreSQL integration

Frontend:
- TypeScript
- ESLint
- Vitest coverage
- Playwright Chromium + Firefox
- axe accessibility
- npm audit/OSV
- bundle size budget

Repo:
- markdownlint
- links
- secret scan
- CodeQL
- SBOM
- license scan
- dependency review
- branch protection
```

Cobertura não garante qualidade, mas regras clínicas sem teste de decisão não podem ser liberadas.

---

## 12. CI/CD e governança

## 12.1 Pontos positivos

- Linux e Windows;
- backend e frontend;
- E2E;
- smoke;
- preflight;
- checks de texto, links e assets;
- lockfiles;
- release gate.

## 12.2 Problemas

- script exige estar na `main` e faz push direto;
- sem PR obrigatório;
- sem reviewer independente;
- sem CODEOWNERS clínico;
- sem ambiente protegido;
- sem assinatura/verificação de artefato;
- sem provenance de build;
- sem SBOM;
- sem release reproducível;
- sem security scans;
- sem teste migration;
- versão hardcoded em script;
- asset checker hardcoded em versão errada;
- Actions não pinadas por SHA;
- não há status de CI recuperado para o commit atual pela integração.

## 12.3 Modelo recomendado

```text
feature branch
    ↓
pull request
    ↓
CI completo + clinical rule tests + security
    ↓
CODEOWNERS técnico + clínico para regras
    ↓
merge protegido
    ↓
tag assinada
    ↓
build reproduzível + SBOM + provenance
    ↓
release draft
    ↓
aprovação
```

---

## 13. Documentação

## 13.1 Qualidade

A documentação é extensa e mostra responsabilidade ao declarar limites. Isso é uma força.

## 13.2 Problema principal

Existe documentação demais sobre versões passadas dentro da árvore principal, enquanto o índice
corrente não representa todo o corpus. O README funciona parcialmente como:

- apresentação;
- manual do usuário;
- arquitetura;
- release note;
- galeria;
- changelog;
- checklist.

Isso torna a documentação datada e difícil de manter.

## 13.3 Estrutura proposta

```text
README.md
docs/
  README.md
  product/
    overview.md
    personas.md
    workflows.md
    limitations.md
  architecture/
    context.md
    containers.md
    modules.md
    decisions/
  clinical/
    safety-model.md
    rule-lifecycle.md
    dose-model.md
    alert-governance.md
  security/
    threat-model.md
    privacy.md
    access-control.md
    incident-response.md
  interoperability/
    fhir-scope.md
    implementation-guide.md
    cds-hooks.md
  operations/
    setup.md
    deployment.md
    backup-restore.md
    observability.md
  contributing/
    clinical-rules.md
    engineering.md
  history/
    audits/
    old-plans/
```

### README ideal

- o que é;
- o que não é;
- screenshot principal;
- 5–8 capacidades;
- instalação rápida;
- segurança/demo;
- arquitetura resumida;
- link para docs;
- licença.

Sem repetir detalhes de cada versão.

---

## 14. Correção completa do versionamento para v0.8.6

## 14.1 Alterações de código

- `backend/app/core/version.py`;
- `backend/pyproject.toml`;
- `frontend/package.json`;
- lockfile do frontend;
- `frontend/src/config/appVersion.ts`;
- schemas/defaults;
- templates de relatório;
- release preflight;
- scripts de captura/check assets;
- testes com strings de versão.

## 14.2 Alterações de documentação

- README;
- docs index;
- release note;
- acceptance matrix;
- traceability;
- accessibility;
- performance;
- audit reports;
- transaction docs;
- roadmap atual;
- credits/assets README.

## 14.3 Assets

Renomear:

```text
docs/assets/v8.6.0/ -> docs/assets/v0.8.6/
*-v8.6.0.* -> *-v0.8.6.*
```

Atualizar todos os links e hashes.

## 14.4 Tags e release

Se a tag/release errada foi publicada:

- preservar registro transparente do erro;
- criar commit corretivo;
- avaliar remoção da tag errada apenas se não houver consumidores;
- publicar `v0.8.6` apontando para o commit correto;
- marcar a release errada como retirada/corrigida;
- não fingir que nunca existiu;
- não reescrever artefatos consumidos sem aviso.

## 14.5 Fonte única

Criar `VERSION` na raiz ou usar metadata canônica e script de geração:

```text
VERSION = 0.8.6
```

CI deve falhar se backend, frontend, docs correntes e tag divergirem. Não incluir policy version no
mesmo mecanismo.

---

## 15. Arquitetura alvo recomendada

Manter um **modular monolith**. Microserviços agora aumentariam a complexidade sem resolver a
consistência clínica.

```text
prescripta/
├── identity_access
├── organizations
├── patients
├── encounters
├── clinical_facts
├── medication_catalog
├── medication_orders
├── terminology
├── rule_registry
├── decision_support
├── protocols
├── reconciliation
├── reports
├── evidence
├── audit
├── integrations
└── ai_assistance
```

### Regras de dependência

- frontend nunca decide risco;
- rotas não contêm regra;
- repositórios não fazem commit;
- serviços de domínio não conhecem HTTP;
- IA nunca cria fato validado;
- relatórios só usam snapshot;
- integração não escreve dado validado sem reconciliação;
- policies e regras são versionadas;
- toda decisão tem cobertura e abstention;
- toda alteração clínica tem provenance.

### Componentes externos opcionais

- PostgreSQL;
- Redis apenas quando necessário;
- object storage;
- terminology server;
- HAPI FHIR/Medplum como camada FHIR, se interoperabilidade real entrar;
- OIDC provider;
- observability stack.

---

## 16. Plano de execução

## Fase 0 — Correção imediata da v0.8.6

Objetivo: corrigir release e impedir falsa segurança.

- normalizar versão;
- decisão canônica;
- bloquear contradições;
- unit model mínimo;
- abstention por sexo/dados/unidade;
- snapshot imutável;
- transação única;
- autorização por objeto mínima;
- SSRF;
- startup seguro;
- testes P0;
- docs honestos;
- retirar claims ambíguos de FHIR/CDS.

## Fase 1 — Fundação v0.9

- Alembic;
- PostgreSQL;
- Unit of Work;
- modelo de fatos clínicos;
- rule registry;
- terminologia;
- papel farmacêutico;
- organização/tenant;
- audit canônico;
- object storage;
- OIDC;
- observabilidade;
- backup/restore.

## Fase 2 — Interoperabilidade controlada

- FHIR R4;
- perfis;
- validator;
- SMART;
- CDS Hooks;
- Provenance/AuditEvent;
- idempotência;
- terminology server;
- contracts/consumer-driven tests.

## Fase 3 — Validação clínica

- finalidade de uso;
- classificação regulatória;
- clinical safety officer;
- hazard log;
- dataset;
- gold standard;
- avaliação por especialidade;
- human factors;
- pilotagem;
- monitoramento;
- QMS;
- change control.

---

## 17. Critérios de aceite para chamar a próxima entrega de v0.8.6

A release só deveria ser considerada consistente quando:

- [ ] nenhuma referência corrente usa `v8.6.0`;
- [ ] tags/assets/metadados estão alinhados;
- [ ] policy version não depende da app version;
- [ ] um único status agrega todos os motores;
- [ ] `CRITICAL` e hard block nunca coexistem com decisão favorável;
- [ ] unidades incompatíveis retornam abstention;
- [ ] sexo ausente não é imputado;
- [ ] falta de regra/fonte não gera “sem risco”;
- [ ] CDS não aceita conhecimento clínico como verdade do cliente;
- [ ] EvidenceBundle é snapshot imutável;
- [ ] relatório é reproduzível pelo hash;
- [ ] checagem e auditoria são transacionais;
- [ ] endpoints por ID possuem autorização por objeto;
- [ ] default secret/seed/SQLite falham fora de demo;
- [ ] SSRF está bloqueado;
- [ ] frontend não envia decisão para a IA;
- [ ] token/session está documentado como demo ou endurecido;
- [ ] lint real existe;
- [ ] testes negativos clínicos e de segurança passam;
- [ ] documentação corrente é version-neutral;
- [ ] limitações são visíveis na UI e nos artefatos.

---

## 18. Backlog resumido por prioridade

### P0

1. corrigir versão;
2. criar ClinicalDecisionOrchestrator;
3. criar `coverage_status`;
4. impedir “released” sem cobertura;
5. corrigir modelo dimensional de dose;
6. abstention para sexo ausente;
7. reescrever CDS para conhecimento server-side;
8. snapshot de decisão;
9. transação atômica;
10. object-level authorization;
11. startup seguro;
12. SSRF protection;
13. testes P0.

### P1

14. Alembic/PostgreSQL;
15. rule registry;
16. separar catálogo e conhecimento;
17. remover código morto;
18. consolidar normalização;
19. papel farmacêutico;
20. workflow de override/coassinatura;
21. OIDC/session hardening;
22. audit event canônico;
23. RAG versionado;
24. AI payload canônico;
25. paginação;
26. N+1;
27. lint/coverage/security CI;
28. docs cleanup;
29. branch protection/governança;
30. observabilidade/backup.

### P2

31. FHIR R4 conformante;
32. SMART;
33. CDS Hooks;
34. terminology server;
35. object storage;
36. eMAR/administração;
37. specialty modules;
38. clinical validation;
39. regulatory/QMS;
40. post-deployment monitoring.

---

## 19. Comparação externa — lições práticas

| Referência | O que demonstra | Lição para o Prescripta |
|---|---|---|
| HL7 FHIR Medication resources | pedido, uso, administração, dispensação e conhecimento são eventos/recursos diferentes | desmontar `MedicationModel` monolítico |
| FHIR Provenance/AuditEvent | criação do dado e uso/acesso têm finalidades distintas | separar provenance clínico de audit de segurança |
| SMART App Launch | scopes e contexto limitam acesso | sair de quatro papéis globais |
| CDS Hooks | cards, sugestões, fonte, feedback e override | tornar o CDS interoperável e mensurável |
| HAPI FHIR | validação de perfis e terminologia versionada | não validar FHIR “na mão” |
| OpenMRS | módulos separados e FHIR dedicado | modular monolith e contratos estáveis |
| OpenEMR CDR | regras sobre múltiplos fatos clínicos | rule registry, eventos e métricas |
| Bahmni | FHIR R4, SNOMED/terminology e CDS separado | terminologia como serviço e CDS desacoplado |
| WHO Medication Without Harm | alto risco, polifarmácia e transição de cuidado | priorizar esses fluxos, não volume de regras |
| ONC SAFER | identificação, CPOE/CDS, follow-up e contingência | criar safety checklist operacional |
| OWASP API Top 10 | BOLA, property exposure, SSRF, auth | testar autorização e egress |
| NIST SSDF | segurança integrada ao SDLC | transformar segurança em gate |
| ANVISA SaMD | software clínico pode demandar regularização | manter finalidade/claims sob controle |
| COFEN 801/2026 | enfermeiro prescreve sob protocolo e requisitos | policy por profissão+protocolo+instituição |
| CFP | prontuário único mínimo e material exclusivo | segregação de registros psicológicos |

---

## 20. Referências principais consultadas

### Repositório

- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/core/auth.py`
- `backend/app/core/version.py`
- `backend/app/core/constants.py`
- `backend/app/database/session.py`
- `backend/app/database/models.py`
- `backend/app/domain/*`
- `backend/app/schemas/*`
- `backend/app/repositories/*`
- `backend/app/services/risk_engine.py`
- `backend/app/services/dose_calculator.py`
- `backend/app/services/dose_intelligence.py`
- `backend/app/services/psychotropic_safety.py`
- `backend/app/services/prescribing_policy.py`
- `backend/app/services/allergy_checker.py`
- `backend/app/services/interaction_checker.py`
- `backend/app/services/normalizer.py`
- `backend/app/services/text.py`
- `backend/app/services/ai_settings.py`
- `backend/app/services/ai_explainer.py`
- `backend/app/services/patient_history_service.py`
- `backend/app/services/emergency_protocol_service.py`
- `backend/app/knowledge/retriever.py`
- `backend/app/knowledge/rag_service.py`
- `backend/app/reports/*`
- `backend/app/integrations/*`
- `backend/app/api/routes/*`
- `backend/tests/*`
- `frontend/src/*`
- `frontend/e2e/critical-flows.spec.ts`
- `.github/workflows/ci.yml`
- `scripts/release_preflight.py`
- `scripts/check_assets.py`
- `scripts/check_markdown_links.py`
- `docs/*`

### Padrões e fontes externas

- WHO Medication Without Harm:
  https://www.who.int/initiatives/medication-without-harm
- WHO Medication safety in high-risk situations:
  https://www.who.int/initiatives/medication-without-harm/medication-safety-in-high-risk-situations
- WHO transitions of care:
  https://www.who.int/publications/i/item/WHO-UHC-SDS-2019.9
- WHO polypharmacy:
  https://www.who.int/publications/i/item/WHO-UHC-SDS-2019.11
- ONC SAFER Guides:
  https://healthit.gov/clinical-quality-and-safety/safer-guides/
- HL7 FHIR MedicationRequest:
  https://hl7.org/fhir/medicationrequest.html
- HL7 FHIR MedicationAdministration:
  https://hl7.org/fhir/medicationadministration.html
- HL7 FHIR MedicationStatement:
  https://hl7.org/fhir/medicationstatement.html
- HL7 FHIR MedicationKnowledge:
  https://hl7.org/fhir/medicationknowledge.html
- HL7 FHIR Provenance:
  https://hl7.org/fhir/provenance.html
- SMART App Launch:
  https://hl7.org/fhir/smart-app-launch/
- CDS Hooks:
  https://cds-hooks.org/specification/current/
- OWASP API Security Top 10:
  https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- NIST SSDF:
  https://csrc.nist.gov/pubs/sp/800/218/final
- ANVISA, Manual SaMD versão 1.3:
  https://www.gov.br/anvisa/pt-br/centraisdeconteudo/publicacoes/produtos-para-a-saude/manuais/manual-regularizacao-gquip/view
- COFEN Resolução 801/2026:
  https://www.cofen.gov.br/resolucao-cofen-no-801-de-14-de-janeiro-de-2026/
- CFP Manual Orientativo de Registro:
  https://site.cfp.org.br/publicacao/manual-orientativo-de-registro-e-elaboracao-de-documentos-psicologicos/
- OpenMRS:
  https://openmrs.org/
- OpenEMR Clinical Decision Rules:
  https://www.open-emr.org/features/cdr/
- HAPI FHIR:
  https://hapifhir.io/hapi-fhir/docs/server_jpa/introduction.html
- Bahmni:
  https://bahmni.atlassian.net/wiki/
- Meta-análise de override de alertas DDI:
  https://pubmed.ncbi.nlm.nih.gov/38899788/

---

## 21. Conclusão final

A `v0.8.6` pode e deve preservar o salto de maturidade funcional e visual que foi implementado.
O erro foi o número `v8.6.0`, não a evolução do produto.

Porém, a auditoria mostra que a próxima melhoria não deve ser outra camada de funcionalidades
paralelas. O Prescripta precisa agora de **convergência**:

- uma decisão;
- uma semântica de dose;
- uma fonte de verdade;
- uma transação;
- um snapshot;
- uma política de acesso;
- um lifecycle de regra;
- uma arquitetura documental;
- uma definição explícita de cobertura.

Com essas correções, ele pode se tornar um projeto de portfólio excepcional e uma base de pesquisa
séria. Sem elas, continuar adicionando especialidades e regras aumenta a aparência de maturidade,
mas também amplia a superfície de falsa segurança, inconsistência e manutenção.
