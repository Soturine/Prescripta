# Deduplicação E Normalização

Prescripta v0.4.0 adiciona normalização simples para reduzir duplicidade e preservar histórico.

## Normalização

O backend normaliza:

- nomes de medicamentos;
- classes e princípios ativos;
- alergias;
- reações adversas;
- comorbidades;
- órgãos e sistemas;
- termos com acento/sem acento;
- sinônimos simples.

Exemplos:

- `Nimesulida`, `nimesulida`, `NIMESULIDA` -> `nimesulida`
- `rim`, `rins`, `insuficiência renal` -> `renal`
- `fígado`, `figado`, `hepático` -> `hepatico`

## Deduplicação

- listas clínicas são deduplicadas por termo normalizado;
- triagem rápida preserva alergias, medicamentos contínuos e reações anteriores;
- cadastro de paciente bloqueia duplicidade simples por nome normalizado e idade/data;
- atualização de perfil clínico gera auditoria.

## Medicamentos v0.8.1

A deduplicação clínica usa uma tabela curada BR para aliases comuns:

- Novalgina -> dipirona;
- Anador -> dipirona;
- Dorflex -> dipirona;
- Neosaldina -> dipirona;
- Lisador -> dipirona;
- metamizol/metamizole -> dipirona.

O valor original é preservado no payload importado, mas a reconciliação usa o
princípio ativo normalizado para detectar duplicidade.

## Condições v0.8.1

Condições importadas passam por vocabulário controlado para categorias renal,
hepática, cardíaca, gastrointestinal, saúde mental e reprodutivo/ginecológica.
Quando há conflito com campo estruturado existente, a decisão fica manual.

## Preservação De Histórico

A triagem rápida não apaga dados existentes. Ela mescla novos itens, registra antes/depois em auditoria e sinaliza conflitos básicos para revisão.
