# Concept sets e terminologia

Concept sets substituem busca textual livre na definição de coortes. Cada conjunto tem
domínio, versões terminológicas, membros, exclusões, regra de descendentes, fontes,
licença, provenance e hash canônico.

Sistemas preparados: CID-10/ICD-10, SNOMED CT, LOINC, RxNorm, ATC e identificadores
OMOP. A aplicação não redistribui vocabulários licenciados; seeds e testes usam apenas
fixtures fictícias claramente marcadas.

O lifecycle é `terminology_matched -> human_reviewed ->
approved_for_demo_study`. Sugestões de IA, quando usadas, começam como draft e nunca são
autoridade de código clínico. Uma versão revisada é imutável.
