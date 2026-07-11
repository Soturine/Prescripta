# Identificadores e Matching de Pacientes

`PatientIdentifier` armazena:

- tipo;
- hash do valor sensivel;
- sistema emissor;
- mascara de exibicao;
- marcador primario.

Tipos permitidos incluem `internal_record_number`, `hospital_record_number`, `insurance_member_number`, `CNS`, `CPF` e `external_system_id`.

Nome + data de nascimento não sao suficientes para mesclagem automatica. O `PatientMatchingService` retorna candidatos, score e motivos, mas exige revisão humana.
