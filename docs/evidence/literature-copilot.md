# Literature Copilot

O workspace aceita apenas `EvidenceSource` registrado e do mesmo tenant. A extração estruturada
produz campos e claims com `source_id`, locator (página/seção) e status de suporte. Ausência de apoio
vira `not_found`; o conteúdo-fonte não é persistido, somente seu hash e a extração revisável.

Texto recuperado pode conter prompt injection. Ele é tratado como conteúdo, marcado e nunca altera
policy, papel, fontes ou instruções. A síntese apresenta claims suportados e lacunas; não cria guideline,
conduta ou recomendação clínica.
