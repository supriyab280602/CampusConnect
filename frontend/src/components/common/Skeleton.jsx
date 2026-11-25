import React from 'react';

export function Skeleton({
  variant = 'text',
  className = '',
}) {
  const baseStyles = 'animate-pulse bg-soft-sand/70 rounded';

  const variantStyles = {
    text: 'h-4 w-full',
    title: 'h-6 w-3/4',
    avatar: 'w-10 h-10 rounded-full',
    card: 'h-32 w-full rounded-xl',
  }[variant] || 'h-4 w-full';

  return <div className={`${baseStyles} ${variantStyles} ${className}`} />;
}
