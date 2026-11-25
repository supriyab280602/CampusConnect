import React from 'react';
import { Button } from './Button';

export function EmptyState({
  title = 'No items found',
  description = 'There are no records to display at this time.',
  actionLabel,
  onAction,
  icon,
  className = '',
}) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 sm:p-10 text-center bg-white/60 border border-soft-sand rounded-lg shadow-subtle ${className}`}>
      {icon ? (
        <div className="mb-3 text-iron-grey">{icon}</div>
      ) : (
        <div className="w-11 h-11 mb-3 rounded-full bg-soft-sand/70 border border-soft-sand flex items-center justify-center text-iron-grey font-serif text-base select-none">
          &empty;
        </div>
      )}
      <h3 className="text-base font-serif font-semibold text-shadow-grey mb-1">
        {title}
      </h3>
      <p className="text-xs text-iron-grey max-w-sm mb-4 leading-relaxed font-sans">
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="outline" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
