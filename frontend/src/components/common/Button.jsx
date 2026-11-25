import React from 'react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  disabled = false,
  loading = false,
  onClick,
  className = '',
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-md transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs tracking-normal',
    md: 'px-4 py-2 text-sm tracking-normal',
    lg: 'px-5 py-2.5 text-sm sm:text-base font-semibold',
  }[size] || 'px-4 py-2 text-sm';

  const variantStyles = {
    primary: 'bg-vivid-tangerine text-white hover:bg-[#E56E0A] focus-visible:ring-vivid-tangerine shadow-subtle active:translate-y-px',
    secondary: 'bg-soft-sand/80 text-shadow-grey hover:bg-soft-sand border border-soft-sand focus-visible:ring-iron-grey active:translate-y-px',
    crimson: 'bg-deep-crimson text-white hover:bg-[#77111A] focus-visible:ring-deep-crimson shadow-subtle active:translate-y-px',
    outline: 'border border-soft-sand bg-white text-shadow-grey hover:bg-warm-porcelain hover:border-iron-grey/40 focus-visible:ring-iron-grey shadow-subtle active:translate-y-px',
    danger: 'bg-deep-crimson text-white hover:bg-[#77111A] focus-visible:ring-deep-crimson shadow-subtle active:translate-y-px',
    ghost: 'text-iron-grey hover:text-shadow-grey hover:bg-soft-sand/50 focus-visible:ring-iron-grey',
  }[variant] || 'bg-vivid-tangerine text-white hover:bg-[#E56E0A]';

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
      )}
      {children}
    </button>
  );
}
