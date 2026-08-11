# Pacote de pesquisa reproduzível v0.9.1

O plano fixa `cohort_run_id`, o run de Data Quality exatamente compatível e as versões revisadas de
cada outcome. Uma versão nova de outcome ou um finding de outro estudo/run não altera nem bloqueia
retroativamente essa análise.

O pacote agregado v2 contém estudo, protocolo, coorte, referências de concept sets, outcomes, plano,
resultados, sumário DQ, proveniência, fontes, limitações, terminologia, mappings, lineage OMOP e matriz
de compatibilidade. O manifesto lista schema version, referências exatas, hashes individuais e hash
canônico do pacote. O verificador recalcula arquivos e detecta arquivo ausente, alterado, não listado,
schema incompatível e lineage adulterado.

Não há linhas de paciente, alegação causal, validade externa, validade clínica ou evidência de mundo
real. Os artefatos são exclusivamente sintéticos/demonstrativos. Hash não equivale a assinatura,
timestamp confiável ou armazenamento WORM.
