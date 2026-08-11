# IPTW experimental

O IPTW suporta estimand ATE ou ATT, pesos estabilizados opcionais e truncamento explícito por
quantis. O output registra modelo, estimand, limites, effective sample size (ESS), distribuição e
contagem de pesos extremos, overlap e SMD antes/depois.

Propensities próximas de 0/1, ESS baixo ou overlap inadequado geram warning ou abstention. ATE e ATT
nunca são misturados. O resultado não é causalmente interpretável sem consistência, positividade,
exchangeability, definição temporal correta e ausência de interferência.

Validação de referência independente permanece pendente (`CAUSAL-207`).
