# Auditoria de Profissionalizacao v0.5.0

## O que deixou de ser generico?

- Medicamentos agora possuem princípio ativo, aliases, fonte, jurisdição e status de validação.
- Campos clínicos genericos foram substituidos por vocabulario controlado.
- RAG interno passou a carregar metadados rastreaveis.

## Como o vocabulario controlado melhorou o sistema?

O banco armazena codigos consistentes e a interface apresenta labels humanos. Isso reduz ambiguidade e evita respostas finais como `renal` ou `cardiaco`.

## Como o modelo princípio ativo primeiro reduziu duplicacao?

Aliases comerciais apontam para o mesmo `ActiveIngredient`. Assim, Novalgina e Anador podem resolver para dipirona sem duplicar regra clínica.

## O que ainda e demonstrativo?

- Cobertura de medicamentos.
- Evidencias e regras clínicas.
- Lookup Anvisa/DCB assistido.
- RAG textual interno.

## O que ja esta mais proximo de uso profissional controlado?

- Separação entre princípio ativo e produto.
- Fonte/jurisdição/status em evidencias.
- Prioridade BR documentada.
- IA limitada a explicacao.

## O que falta para integracao hospitalar real?

- Ports & Adapters.
- Adapters FHIR/HL7/RNDS/CSV/JSON.
- Consentimento.
- Matching de paciente.
- Auditoria de importação.
- Contratos/API oficiais com sistemas clínicos.

## Riscos remanescentes

- Dados demonstrativos podem ser confundidos com cobertura real.
- Fontes pendentes de revisão exigem governanca.
- Integracoes reais precisam segurança, LGPD e contrato.

## Por que foco Brasil/Anvisa?

Porque o contexto regulatorio brasileiro deve usar fonte brasileira como referencia primaria.

## Como fontes internacionais serao tratadas?

Como apoio secundario, sempre com `jurisdiction` explicita e aviso quando houver conflito.
