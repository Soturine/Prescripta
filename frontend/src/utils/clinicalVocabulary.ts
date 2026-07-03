export type VocabularyOption = {
  value: string;
  label: string;
};

export const renalOptions: VocabularyOption[] = [
  { value: "", label: "Nao informado" },
  { value: "sem_doenca_renal_conhecida", label: "Sem doenca renal conhecida" },
  { value: "doenca_renal_cronica", label: "Doenca renal cronica" },
  { value: "drc_estagio_1", label: "Doenca renal cronica estagio 1" },
  { value: "drc_estagio_2", label: "Doenca renal cronica estagio 2" },
  { value: "drc_estagio_3", label: "Doenca renal cronica estagio 3" },
  { value: "drc_estagio_4", label: "Doenca renal cronica estagio 4" },
  { value: "drc_estagio_5", label: "Doenca renal cronica estagio 5" },
  { value: "hemodialise", label: "Hemodialise" },
  { value: "transplante_renal", label: "Transplante renal" },
  { value: "calculo_renal_recorrente", label: "Calculo renal recorrente" },
  { value: "funcao_renal_a_revisar", label: "Funcao renal a revisar" },
];

export const hepaticOptions: VocabularyOption[] = [
  { value: "", label: "Nao informado" },
  { value: "sem_doenca_hepatica_conhecida", label: "Sem doenca hepatica conhecida" },
  { value: "esteatose_hepatica", label: "Esteatose hepatica" },
  { value: "hepatite", label: "Hepatite" },
  { value: "cirrose", label: "Cirrose" },
  { value: "insuficiencia_hepatica", label: "Insuficiencia hepatica" },
  { value: "enzimas_hepaticas_alteradas", label: "Enzimas hepaticas alteradas" },
  { value: "funcao_hepatica_a_revisar", label: "Funcao hepatica a revisar" },
];

export const cardiacOptions: VocabularyOption[] = [
  { value: "", label: "Nao informado" },
  { value: "sem_doenca_cardiaca_conhecida", label: "Sem doenca cardiaca conhecida" },
  { value: "arritmia", label: "Arritmia" },
  { value: "insuficiencia_cardiaca", label: "Insuficiencia cardiaca" },
  { value: "doenca_arterial_coronariana", label: "Doenca arterial coronariana" },
  { value: "historico_de_infarto", label: "Historico de infarto" },
  { value: "hipertensao", label: "Hipertensao" },
  { value: "risco_cardiovascular_a_revisar", label: "Risco cardiovascular a revisar" },
];

export const gastrointestinalOptions: VocabularyOption[] = [
  { value: "", label: "Nao informado" },
  {
    value: "sem_historico_gastrointestinal_conhecido",
    label: "Sem historico gastrointestinal conhecido",
  },
  { value: "gastrite", label: "Gastrite" },
  { value: "ulcera", label: "Ulcera" },
  { value: "sangramento_gastrointestinal", label: "Sangramento gastrointestinal" },
  { value: "refluxo_importante", label: "Refluxo importante" },
  { value: "doenca_inflamatoria_intestinal", label: "Doenca inflamatoria intestinal" },
  {
    value: "historico_gastrointestinal_a_revisar",
    label: "Historico gastrointestinal a revisar",
  },
];

export const pregnancyOptions: VocabularyOption[] = [
  { value: "nao_informado", label: "Nao informado" },
  { value: "nao_se_aplica", label: "Nao se aplica" },
  { value: "gestante", label: "Gestante" },
  { value: "lactante", label: "Lactante" },
  { value: "possibilidade_a_confirmar", label: "Possibilidade a confirmar" },
];

export const clinicalVocabularyLabels = Object.fromEntries(
  [
    ...renalOptions,
    ...hepaticOptions,
    ...cardiacOptions,
    ...gastrointestinalOptions,
    ...pregnancyOptions,
  ].map((option) => [option.value, option.label]),
);

export function formatClinicalValue(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return clinicalVocabularyLabels[value] ?? value;
}
