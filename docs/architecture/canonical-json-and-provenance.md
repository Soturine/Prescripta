# JSON canônico, hashes e provenance

O algoritmo `sha256-canonical-json-v1` serializa JSON em UTF-8, ordena chaves, remove
espaços não semânticos, rejeita NaN e converte datas, decimais e enums para formas
estáveis. Em seguida calcula SHA-256.

Ele é usado em versões de protocolo, concept sets, coortes, outcomes, planos, runs,
snapshots e interações de IA. O hash demonstra igualdade do conteúdo serializado; não é
assinatura digital e não prova autoria.

Resultados importantes carregam autoria, horário, versão, fontes, definição, engine,
marcador do dataset, uso de IA/provider e estado de revisão humana. Snapshots revisados
ou executados são imutáveis; correções produzem novas versões.
