export type VocabularyOption = {
  value: string;
  label: string;
};

export const renalOptions: VocabularyOption[] = [
  { value: "", label: "Não informado" },
  { value: "sem_doenca_renal_conhecida", label: "Sem doença renal conhecida" },
  { value: "doenca_renal_cronica", label: "Doença renal crônica" },
  { value: "drc_estagio_1", label: "Doença renal crônica estágio 1" },
  { value: "drc_estagio_2", label: "Doença renal crônica estágio 2" },
  { value: "drc_estagio_3", label: "Doença renal crônica estágio 3" },
  { value: "drc_estagio_4", label: "Doença renal crônica estágio 4" },
  { value: "drc_estagio_5", label: "Doença renal crônica estágio 5" },
  { value: "hemodialise", label: "Hemodiálise" },
  { value: "transplante_renal", label: "Transplante renal" },
  { value: "calculo_renal_recorrente", label: "Cálculo renal recorrente" },
  { value: "funcao_renal_a_revisar", label: "Função renal a revisar" },
];

export const hepaticOptions: VocabularyOption[] = [
  { value: "", label: "Não informado" },
  { value: "sem_doenca_hepatica_conhecida", label: "Sem doença hepática conhecida" },
  { value: "esteatose_hepatica", label: "Esteatose hepática" },
  { value: "hepatite", label: "Hepatite" },
  { value: "cirrose", label: "Cirrose" },
  { value: "insuficiencia_hepatica", label: "Insuficiência hepática" },
  { value: "enzimas_hepaticas_alteradas", label: "Enzimas hepáticas alteradas" },
  { value: "funcao_hepatica_a_revisar", label: "Função hepática a revisar" },
];

export const cardiacOptions: VocabularyOption[] = [
  { value: "", label: "Não informado" },
  { value: "sem_doenca_cardiaca_conhecida", label: "Sem doença cardíaca conhecida" },
  { value: "arritmia", label: "Arritmia" },
  { value: "insuficiencia_cardiaca", label: "Insuficiência cardíaca" },
  { value: "doenca_arterial_coronariana", label: "Doença arterial coronariana" },
  { value: "historico_de_infarto", label: "Histórico de infarto" },
  { value: "hipertensao", label: "Hipertensão" },
  { value: "risco_cardiovascular_a_revisar", label: "Risco cardiovascular a revisar" },
];

export const gastrointestinalOptions: VocabularyOption[] = [
  { value: "", label: "Não informado" },
  {
    value: "sem_historico_gastrointestinal_conhecido",
    label: "Sem histórico gastrointestinal conhecido",
  },
  { value: "gastrite", label: "Gastrite" },
  { value: "ulcera", label: "Úlcera" },
  { value: "sangramento_gastrointestinal", label: "Sangramento gastrointestinal" },
  { value: "refluxo_importante", label: "Refluxo importante" },
  { value: "doenca_inflamatoria_intestinal", label: "Doença inflamatória intestinal" },
  {
    value: "historico_gastrointestinal_a_revisar",
    label: "Histórico gastrointestinal a revisar",
  },
];

export const pregnancyOptions: VocabularyOption[] = [
  { value: "nao_informado", label: "Não informado" },
  { value: "nao_se_aplica", label: "Não se aplica" },
  { value: "gestante", label: "Gestante" },
  { value: "lactante", label: "Lactante" },
  { value: "possibilidade_a_confirmar", label: "Possibilidade a confirmar" },
];

export const mentalHealthOptions: VocabularyOption[] = [
  { value: "depressao", label: "Depressão" },
  { value: "ansiedade", label: "Ansiedade" },
  { value: "transtorno_bipolar", label: "Transtorno bipolar" },
  { value: "epilepsia_convulsoes", label: "Epilepsia/convulsões" },
  { value: "risco_sedacao", label: "Risco de sedação" },
  { value: "risco_serotoninergico", label: "Risco serotoninérgico" },
  { value: "uso_isrs", label: "Uso de ISRS" },
  { value: "uso_imao", label: "Uso de IMAO" },
  { value: "uso_antipsicotico", label: "Uso de antipsicótico" },
  { value: "uso_estabilizador_humor", label: "Uso de estabilizador de humor" },
  { value: "risco_neuropsiquiatrico_a_revisar", label: "Risco neuropsiquiátrico a revisar" },
];

export const reproductiveGynecologicOptions: VocabularyOption[] = [
  { value: "gestante", label: "Gestante" },
  { value: "lactante", label: "Lactante" },
  { value: "tentando_engravidar", label: "Tentando engravidar" },
  { value: "uso_anticoncepcional_hormonal", label: "Uso de anticoncepcional hormonal" },
  { value: "diu_hormonal", label: "DIU hormonal" },
  { value: "diu_nao_hormonal", label: "DIU não hormonal" },
  { value: "endometriose", label: "Endometriose" },
  { value: "sop", label: "Síndrome dos ovários policísticos" },
  { value: "ciclo_irregular", label: "Ciclo irregular" },
  { value: "tratamento_hormonal", label: "Tratamento hormonal" },
  { value: "risco_trombotico", label: "Risco trombótico" },
  { value: "quadro_ginecologico_a_revisar", label: "Quadro ginecológico a revisar" },
];

export const clinicalVocabularyLabels = Object.fromEntries(
  [
    ...renalOptions,
    ...hepaticOptions,
    ...cardiacOptions,
    ...gastrointestinalOptions,
    ...pregnancyOptions,
    ...mentalHealthOptions,
    ...reproductiveGynecologicOptions,
  ].map((option) => [option.value, option.label]),
);

export function formatClinicalValue(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return clinicalVocabularyLabels[value] ?? value;
}
