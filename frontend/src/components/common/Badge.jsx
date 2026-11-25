import React from 'react';

export function Badge({
  children,
  variant = 'neutral',
  size = 'sm',
  className = '',
}) {
  const variantStyles = {
    neutral: 'bg-soft-sand/50 text-iron-grey border-soft-sand/80',
    accent: 'bg-red-50/80 text-deep-crimson border-red-200/60',
    primary: 'bg-iron-grey/10 text-shadow-grey border-iron-grey/20',
    crimson: 'bg-[#8E151F]/10 text-deep-crimson border-[#8E151F]/20',
    success: 'bg-emerald-50/90 text-emerald-800 border-emerald-200/70',
    danger: 'bg-red-50/90 text-deep-crimson border-red-200/70',
  }[variant] || 'bg-soft-sand/50 text-iron-grey border-soft-sand/80';

  const sizeStyles = {
    xs: 'px-2 py-0.5 text-[10px] tracking-wide font-medium',
    sm: 'px-2.5 py-0.5 text-[11px] tracking-normal font-medium',
    md: 'px-3 py-1 text-xs tracking-normal font-medium',
  }[size] || 'px-2.5 py-0.5 text-[11px]';

  return (
    <span className={`inline-flex items-center rounded-md border ${sizeStyles} ${variantStyles} ${className}`}>
      {children}
    </span>
  );
}
