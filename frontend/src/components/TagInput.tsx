import type { InputHTMLAttributes } from "react";

import { splitList } from "../utils/formatters";

type TagInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  valuePreview?: string;
};

export default function TagInput({ label, valuePreview, ...props }: TagInputProps) {
  const tags = splitList(valuePreview ?? String(props.defaultValue ?? ""));
  return (
    <label className="grid gap-1.5">
      <span className="label">{label}</span>
      <input className="field" {...props} />
      {tags.length ? (
        <span className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span
              className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700"
              key={tag}
            >
              {tag}
            </span>
          ))}
        </span>
      ) : null}
    </label>
  );
}
