import type { InputHTMLAttributes } from "react";

type AutocompleteProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  listId: string;
  options: string[];
  error?: string;
};

export default function Autocomplete({
  label,
  listId,
  options,
  error,
  ...props
}: AutocompleteProps) {
  return (
    <label className="grid gap-1.5">
      <span className="label">{label}</span>
      <input className="field" list={listId} {...props} />
      <datalist id={listId}>
        {options.map((option) => (
          <option key={option} value={option} />
        ))}
      </datalist>
      {error ? <span className="text-xs text-danger">{error}</span> : null}
    </label>
  );
}
