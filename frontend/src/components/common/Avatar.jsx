import React from 'react';

export function Avatar({
  name = '',
  size = 'md',
  className = '',
}) {
  const getInitials = (str) => {
    if (!str) return 'CC';
    const parts = str.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const sizeStyles = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-13 h-13 text-base',
    xl: 'w-18 h-18 text-xl',
  }[size] || 'w-10 h-10 text-sm';

  // Academic palette tones (restrained, no neon orange)
  const colors = [
    'bg-shadow-grey text-warm-porcelain border border-soft-sand/40',
    'bg-iron-grey text-white border border-soft-sand/40',
    'bg-deep-crimson text-warm-porcelain border border-soft-sand/40',
    'bg-[#404D54] text-warm-porcelain border border-soft-sand/40',
    'bg-ash-grey text-shadow-grey border border-iron-grey/25',
  ];
  const charCode = name ? name.charCodeAt(0) : 0;
  const colorClass = colors[charCode % colors.length];

  return (
    <div className={`inline-flex items-center justify-center rounded-full font-serif font-medium tracking-tight flex-shrink-0 select-none shadow-subtle ${sizeStyles} ${colorClass} ${className}`}>
      {getInitials(name)}
    </div>
  );
}
