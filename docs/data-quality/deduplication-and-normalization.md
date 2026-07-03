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

## Preservação De Histórico

A triagem rápida não apaga dados existentes. Ela mescla novos itens, registra antes/depois em auditoria e sinaliza conflitos básicos para revisão.
