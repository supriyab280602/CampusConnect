import React from 'react';

export function Card({
  children,
  className = '',
  onClick,
  hover = false,
  variant = 'default',
}) {
  const variantStyles = {
    default: 'bg-white border border-soft-sand/90 shadow-card',
    subtle: 'bg-white/70 border border-soft-sand/70',
    elevated: 'bg-white border border-soft-sand shadow-elevated',
    flat: 'bg-white border border-soft-sand/60',
  }[variant] || 'bg-white border border-soft-sand/90 shadow-card';

  return (
    <div
      onClick={onClick}
      className={`rounded-lg p-4 sm:p-5 transition-all ${variantStyles} ${
        hover ? 'hover:border-iron-grey/40 hover:shadow-subtle cursor-pointer' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}
