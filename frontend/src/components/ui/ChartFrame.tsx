import { useId, type ReactNode } from "react";

export default function ChartFrame({
  title,
  description,
  children,
  fallback,
}: {
  title: string;
  description: string;
  children: ReactNode;
  fallback: ReactNode;
}) {
  const titleId = useId();
  const descriptionId = useId();
  return (
    <figure aria-describedby={descriptionId} aria-labelledby={titleId} className="border-t border-slate-200 pt-4">
      <figcaption>
        <h3 className="text-sm font-black text-ink" id={titleId}>{title}</h3>
        <p className="mt-1 text-xs text-slate-600" id={descriptionId}>{description}</p>
      </figcaption>
      <div aria-hidden="true" className="mt-4">{children}</div>
      <div className="mt-4 overflow-x-auto">{fallback}</div>
    </figure>
  );
}
