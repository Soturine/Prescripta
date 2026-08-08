# Evidence Intelligence

A fundação de evidências da v0.8.8 separa a identidade de uma fonte do vínculo entre essa fonte e um
objeto do produto. `EvidenceSource` armazena metadados e `EvidenceLink` relaciona a fonte a protocolo,
estudo, concept set, outcome ou outro alvo permitido.

Fontes e vínculos são institucionais, começam como `pending_review` e carregam autoria e timestamps.
Identificadores repetidos e vínculos duplicados são recusados no banco. APIs de listagem são
paginadas e restritas por capacidade.

Esta camada é provenance, não um motor de decisão. Um vínculo não prova qualidade metodológica nem
aprova conduta. Conteúdo recuperado continua sujeito a jurisdição, licença, vigência e revisão humana.

Veja também [modelo de fontes](source-model.md) e [concept sets](concept-sets.md).
