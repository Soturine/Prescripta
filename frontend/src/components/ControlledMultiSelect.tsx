import type { VocabularyOption } from "../utils/clinicalVocabulary";

type ControlledMultiSelectProps = {
  label: string;
  options: VocabularyOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
};

export default function ControlledMultiSelect({
  label,
  options,
  selected,
  onChange,
}: ControlledMultiSelectProps) {
  function toggle(value: string) {
    if (selected.includes(value)) {
      onChange(selected.filter((item) => item !== value));
      return;
    }
    onChange([...selected, value]);
  }

  return (
    <fieldset className="grid gap-2">
      <legend className="label">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <label
            className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
            key={option.value}
          >
            <input
              checked={selected.includes(option.value)}
              className="h-4 w-4 accent-ocean"
              onChange={() => toggle(option.value)}
              type="checkbox"
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
