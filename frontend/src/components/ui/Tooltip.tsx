import { useId, type ReactNode } from "react";

export default function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  const id = useId();
  return (
    <span className="group/tooltip relative inline-flex" aria-describedby={id}>
      {children}
      <span
        className="pointer-events-none absolute bottom-full left-1/2 z-30 mb-2 hidden w-max max-w-64 -translate-x-1/2 rounded-lg bg-ink px-2.5 py-1.5 text-xs font-medium text-white shadow-lg group-focus-within/tooltip:block group-hover/tooltip:block"
        id={id}
        role="tooltip"
      >
        {label}
      </span>
    </span>
  );
}
