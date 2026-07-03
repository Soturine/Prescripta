import type { SelectHTMLAttributes } from "react";

import type { VocabularyOption } from "../utils/clinicalVocabulary";

type ControlledSelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  options: VocabularyOption[];
  error?: string;
};

export default function ControlledSelect({
  label,
  options,
  error,
  ...props
}: ControlledSelectProps) {
  return (
    <label className="grid gap-1.5">
      <span className="label">{label}</span>
      <select className="field" {...props}>
        {options.map((option) => (
          <option key={option.value || "empty"} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? <span className="text-xs text-danger">{error}</span> : null}
    </label>
  );
}
