# Arquitetura da informação

## Navegação principal

```text
Início
Cuidado e segurança
  Pacientes · Medicamentos · Checagem clínica · Farmácia clínica
Evidência
  Fontes e relatórios
Pesquisa
  Estudos e RWE
Governança
  Reconciliação · Auditoria · IA · Usuários
Ajuda
```

Destinos são derivados das capacidades da sessão. Em mobile, as tarefas principais ficam na barra inferior e o conjunto completo no drawer.

## Profundidade progressiva

A ação e o estado principal aparecem primeiro. Detalhes técnicos, filtros avançados e payload de auditoria ficam em disclosure controlado. A checagem usa cinco etapas: paciente, medicamentos, contexto, checagem e resultado. Research mantém estudos, coortes, concept sets, desfechos, runs, qualidade e proveniência no mesmo workspace conceitual.

## Estados

Loading, vazio, erro, offline e acesso negado têm significados diferentes. Estados vazios são específicos de intervenção, estudo, evidência ou evento e oferecem ação ou ajuda adequada. Resultado vazio nunca é apresentado como ausência de risco.
