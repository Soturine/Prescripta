# Motor de Risco

## Atualizacao v0.7.0

A v0.7.0 adiciona `patient_counseling`, `missing_data_mode` e `contextual_question` na resposta de checagem.

Esses campos sao orientativos. Eles ajudam o profissional a explicar efeitos, atividades de risco e limitacoes por historico incompleto, mas nao alteram:

- `prescription_status`;
- `risk_level`;
- bloqueio;
- severidade;
- dose;
- recomendacao final.

Resumo pratico, perfil funcional e modo sem historico ficam em servicos separados do motor deterministico.

## Atualizacao v0.6.0

O motor passa a considerar, quando os dados existem:

- plano de exposicao, dose acumulada, duracao e uso continuo;
- monitoramento necessario;
- perfil ADME, metabolismo, eliminacao e CYP;
- cautela renal/hepatica por nivel de eliminacao/metabolismo;
- fatores neuropsiquiatricos;
- fatores reprodutivos/ginecologicos;
- regra especifica rifampicina/rifabutina + contraceptivo hormonal;
- identificadores apenas para matching/deduplicacao, nunca para decisao clinica.

Alertas novos sao de revisao profissional. O motor nao afirma que todo antibiotico corta anticoncepcional e nao cria contraindicao psiquiatrica generica sem fonte.

## Atualizacao v0.5.0

O motor passa a considerar metadados de medicamento e paciente mais estruturados:

- principio ativo;
- aliases comerciais;
- fonte e jurisdicao;
- status de validacao da evidencia;
- vocabulario clinico controlado.

Dados antigos ainda sao aceitos quando possivel, mas entradas genericas como `renal`, `cardiaco` e `gastrointestinal` sao normalizadas para codigos controlados, por exemplo `funcao_renal_a_revisar`.

Na saida, o sistema exibe labels humanos em vez dos codigos internos.

O motor de risco fica em `backend/app/services/risk_engine.py`.

## Entradas

- Paciente.
- Medicamento.
- Dose em mg.
- Frequência por dia.
- Via de administração.
- Duração em dias.
- Indicação ou quadro demonstrativo.
- Observações do profissional.

## Regras

- Alergia ao medicamento, princípio ativo ou classe: alerta crítico e bloqueio.
- Dose diária acima da dose máxima: alerta crítico e bloqueio.
- Duração planejada acima do limite demonstrativo: alerta alto.
- Dose acumulada estimada acima do limite acumulado: alerta alto.
- Limite por condição clínica: alerta quando o paciente possui condição com limite específico.
- Interação medicamentosa demonstrativa: alerta alto ou crítico.
- Cinco ou mais medicamentos contínuos: alerta moderado.
- Idade maior ou igual a 65 anos: aumenta risco em um nível.
- Cautela em idosos: alerta quando o medicamento possui esse marcador.
- Condição renal, hepática, cardíaca ou gastrointestinal relacionada à cautela do medicamento: alerta alto ou moderado.
- Reação adversa prévia relacionada ao medicamento, classe ou efeito: alerta alto.
- Comorbidade contraindicada: alerta alto.
- Via não permitida: alerta alto.
- Perfil clínico incompleto: aviso de revisão quando há contexto clínico parcial.

## Saídas

- `prescription_status`: `liberado`, `atencao` ou `bloqueado`.
- `risk_level`: baixo, moderado, alto ou crítico.
- Alertas com severidade, código, mensagem e recomendação.
- Resumo de dose diária, duração e dose acumulada.
- Compatibilidade paciente-medicação.
- Fatores do paciente e do medicamento considerados.
- Clinical Context Graph lógico.

## Compatibilidade

- `alta`: sem riscos relevantes e perfil clínico suficientemente completo.
- `moderada`: alertas altos ou múltiplos moderados.
- `baixa`: bloqueio crítico ou alerta crítico.

Compatibilidade não é liberação automática. Ela organiza sinais para revisão profissional.

## Revisão Humana

Exigida quando o status não é `liberado`, quando a compatibilidade é baixa/moderada ou quando faltam dados relevantes do perfil clínico.

## Observação

As regras são demonstrativas e não clinicamente completas.
