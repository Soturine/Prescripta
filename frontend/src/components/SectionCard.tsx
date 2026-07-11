import type { ReactNode } from "react";

export default function SectionCard({ title, description, children, className = "" }: { title?: string; description?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`surface-card p-5 sm:p-6 ${className}`}>
      {title ? <h2 className="text-lg font-bold text-ink">{title}</h2> : null}
      {description ? <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p> : null}
      <div className={title || description ? "mt-5" : ""}>{children}</div>
    </section>
  );
}
