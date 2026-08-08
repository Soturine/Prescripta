# Reprodutibilidade de Research/RWE

Reprodutibilidade, nesta versão, significa conseguir relacionar um resultado agregado à entrada
serializada que o produziu. Não significa validade externa, causalidade nem reprodução em uma base
clínica real.

Cada execução registra:

- IDs e hashes das versões de protocolo e coorte;
- `data_snapshot_marker` fornecido explicitamente;
- versões das fontes, do engine determinístico e do Prescripta;
- executor, instituição e horário;
- contagem final, agregados e etapas de attrition;
- `run_hash` e um `ResearchSnapshot` sem identificadores de paciente.

O algoritmo `sha256-canonical-json-v1` ordena chaves, normaliza datas, decimais e enums, rejeita
valores não finitos e calcula SHA-256 sobre UTF-8. O hash detecta diferença de conteúdo, mas não é
assinatura digital nem prova autoria.

Protocolos, concept sets e coortes revisados, assim como runs concluídos, não são editados. Uma
correção cria nova versão ou nova execução. A unidade de trabalho da requisição confirma objeto,
eventos de auditoria e relações em um único commit; falha provoca rollback integral.

Para reproduzir um run, é necessário preservar também o dataset indicado pelo marcador. A v0.8.8
persiste o marcador e o snapshot agregado, mas não implementa armazenamento WORM do dataset externo.
