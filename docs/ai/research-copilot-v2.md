# Research Copilot v2

O router recebe tarefa, classificação de dados, fontes permitidas e policy versionada. Suporta drafts
de protocolo/pergunta, sugestão de concept set, extração/síntese de evidência e explicações de
comparação, Data Quality e journey.

- outputs são propostas `pending_review`; nunca executam coorte/query nem publicam estudo;
- conceito sugerido deve existir no registro terminológico autorizado;
- claim de evidência exige `source_id` e locator pertencentes à instituição;
- explicação comparativa só pode repetir números fornecidos pelo motor determinístico;
- dados sensíveis exigem rota local permitida; sem provider elegível, falha fechado;
- provider, modelo, policy, prompt/schema version, sources, hashes, erro sanitizado e revisão ficam
  na provenance; prompt bruto e identificadores reais não.

Conteúdo recuperado é dado não confiável. Instruções nele são ignoradas e sinalizadas, nunca
promovidas a instruções do sistema.
