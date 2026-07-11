type LoadingStateProps = {
  label?: string;
};

export default function LoadingState({ label = "Carregando" }: LoadingStateProps) {
  return (
    <div className="surface-card flex min-h-44 items-center justify-center p-6">
      <div className="grid w-full max-w-sm gap-4">
        <div className="flex items-center justify-center gap-3 text-sm font-semibold text-slate-600">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-ocean border-t-transparent" />
          {label}
        </div>
        <div className="grid gap-2">
          <span className="skeleton-line w-full" />
          <span className="skeleton-line w-4/5" />
          <span className="skeleton-line w-2/3" />
        </div>
      </div>
    </div>
  );
}
