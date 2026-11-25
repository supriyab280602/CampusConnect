import React from 'react';

export function Input({
  label,
  id,
  type = 'text',
  value,
  onChange,
  placeholder = '',
  error = '',
  helperText = '',
  required = false,
  disabled = false,
  className = '',
  ...props
}) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`flex flex-col space-y-1.5 ${className}`}>
      {label && (
        <label htmlFor={inputId} className="text-xs font-semibold text-iron-grey uppercase tracking-wider">
          {label} {required && <span className="text-deep-crimson">*</span>}
        </label>
      )}
      <input
        id={inputId}
        name={props.name || inputId}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={`w-full px-3.5 py-2 text-sm bg-white border rounded-md text-shadow-grey placeholder:text-iron-grey/50 focus:outline-none focus:ring-1 focus:ring-iron-grey focus:border-iron-grey transition-colors ${
          error ? 'border-deep-crimson focus:ring-deep-crimson' : 'border-soft-sand hover:border-ash-grey'
        } ${disabled ? 'bg-soft-sand/40 cursor-not-allowed' : ''}`}
        {...props}
      />
      {error && <span className="text-xs text-deep-crimson font-medium">{error}</span>}
      {!error && helperText && <span className="text-xs text-iron-grey">{helperText}</span>}
    </div>
  );
}
