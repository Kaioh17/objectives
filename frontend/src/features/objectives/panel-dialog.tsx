"use client";

import { useEffect, useRef, type ReactNode } from "react";

// Modal popup (a bottom sheet on phones) for a panel on small screens; the panel brings its own heading
export function PanelDialog({
  label,
  onClose,
  children,
}: {
  label: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  return (
    <dialog
      ref={ref}
      aria-label={label}
      onClose={onClose}
      onClick={(event) => event.target === event.currentTarget && ref.current?.close()}
    >
      {children}
      <button
        type="button"
        className="dialog-close"
        aria-label="Close"
        onClick={() => ref.current?.close()}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M6 6l12 12M18 6 6 18" />
        </svg>
      </button>
    </dialog>
  );
}
