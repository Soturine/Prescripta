import { formatClinicalValue } from "../utils/clinicalVocabulary";

export default function VocabularyBadge({ value }: { value: string | null | undefined }) {
  return (
    <span className="inline-flex min-h-7 items-center rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">
      {formatClinicalValue(value)}
    </span>
  );
}
