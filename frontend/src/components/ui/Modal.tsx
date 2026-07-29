import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";

export default function Modal({
  open,
  title,
  description,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      aria-describedby={description ? descriptionId : undefined}
      aria-labelledby={titleId}
      className="m-auto max-h-[calc(100dvh-2rem)] w-[min(94vw,42rem)] rounded-t-3xl border border-slate-200 bg-white p-0 text-ink shadow-2xl backdrop:bg-slate-950/45 sm:rounded-3xl"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClose={onClose}
      ref={ref}
    >
      <div className="sticky top-0 flex items-start justify-between gap-4 border-b border-slate-200 bg-white px-5 py-4 sm:px-6">
        <div>
          <h2 className="text-lg font-extrabold" id={titleId}>{title}</h2>
          {description ? <p className="mt-1 text-sm text-slate-600" id={descriptionId}>{description}</p> : null}
        </div>
        <button aria-label="Fechar" className="icon-button" onClick={onClose} type="button">
          <X aria-hidden="true" className="h-5 w-5" />
        </button>
      </div>
      <div className="overflow-y-auto p-5 sm:p-6">{children}</div>
    </dialog>
  );
}
