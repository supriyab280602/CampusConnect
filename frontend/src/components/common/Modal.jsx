import React, { useEffect } from 'react';

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = 'max-w-lg',
}) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleEscape);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4 text-center">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-shadow-grey/60 backdrop-blur-xs transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />

        {/* Modal Dialog */}
        <div
          className={`relative w-full ${maxWidth} transform overflow-hidden rounded-xl bg-white p-6 text-left shadow-xl transition-all border border-soft-sand z-10`}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-headline"
        >
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-soft-sand">
            <h3 id="modal-headline" className="text-lg font-serif font-semibold text-shadow-grey">
              {title}
            </h3>
            <button
              type="button"
              onClick={onClose}
              className="text-iron-grey hover:text-shadow-grey text-xl leading-none font-bold p-1 rounded hover:bg-soft-sand/50 transition-colors"
            >
              &times;
            </button>
          </div>
          <div>{children}</div>
        </div>
      </div>
    </div>
  );
}
