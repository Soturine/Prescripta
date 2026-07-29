import type { KeyboardEvent } from "react";

export type TabOption = { id: string; label: string; badge?: string | number };

export default function Tabs({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: TabOption[];
  value: string;
  onChange: (value: string) => void;
}) {
  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? options.length - 1
        : (index + (event.key === 'ArrowRight' ? 1 : -1) + options.length) % options.length;
    onChange(options[nextIndex].id);
    document.getElementById(`tab-${options[nextIndex].id}`)?.focus();
  }

  return (
    <div aria-label={label} className="flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1" role="tablist">
      {options.map((option, index) => (
        <button
          aria-selected={value === option.id}
          className={`min-h-10 shrink-0 rounded-lg px-3 py-2 text-sm font-bold transition ${value === option.id ? 'bg-white text-ink shadow-xs' : 'text-slate-600 hover:text-ink'}`}
          id={`tab-${option.id}`}
          key={option.id}
          onClick={() => onChange(option.id)}
          onKeyDown={(event) => handleKeyDown(event, index)}
          role="tab"
          tabIndex={value === option.id ? 0 : -1}
          type="button"
        >
          {option.label}{option.badge !== undefined ? <span className="ml-2 text-xs text-slate-500">{option.badge}</span> : null}
        </button>
      ))}
    </div>
  );
}
