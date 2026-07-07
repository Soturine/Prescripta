# Taxonomia de Efeitos Adversos

A v0.7.0 adiciona uma taxonomia controlada para orientar resumos praticos.

Categorias:

- `sleep_attention`: insonia, sonolencia, sedacao, atencao/reflexos, tontura, confusao e fadiga.
- `daily_activity`: dirigir, operar maquinas, trabalho em altura, atividade de risco, queda, cuidador e alta atencao.
- `mood_behavior`: humor, ansiedade, irritabilidade, piora psiquiatrica, agitacao, apatia e risco serotoninergico.
- `appetite_weight`: apetite, peso e glicemia.
- `sexual_reproductive`: libido, funcao sexual, ejaculacao, ciclo, contracepcao, gestacao/lactacao e fertilidade.
- `neurologic`: dor de cabeca, tremor, convulsao, parestesia e vertigem.
- `temperature_autonomic`: hipotermia, hipertermia, sudorese e calafrios.
- `cardiovascular_pressure`: hipotensao, hipotensao ortostatica, palpitacao, arritmia e sincope/desmaio.
- `gastrointestinal`: nausea, vomito, diarreia, constipacao, dor abdominal e sangramento GI.
- `renal_hepatic`: cautela/toxicidade/monitoramento renal e hepatico.
- `red_flags`: procurar atendimento, alergia, falta de ar, inchaco, desmaio, sangramento e dor intensa.

O backend normaliza aliases para codigos suportados e descarta categorias fora do contrato. A UI apresenta os codigos para deixar claro que a lista e controlada e demonstrativa.
