# Política de qualidade de release

Uma release só pode ser criada depois do CI concluído e verde para o SHA da `main`. Validação local
é necessária, mas não suficiente. Tags são imutáveis e nunca recebem force push.

Itens sem teste ou evidência recebem `partial`, `not_implemented`, `blocked_by_external_validation`
ou `deferred`. Captura visual não equivale a E2E, regra demo não equivale a validação clínica e
provider configurado não equivale a disponibilidade operacional.

