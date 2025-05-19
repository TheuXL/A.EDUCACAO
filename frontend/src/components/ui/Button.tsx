import React from 'react';
import { cn } from '@/utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'link';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  fullWidth = false,
  children,
  disabled,
  ...props
}: ButtonProps) {
  const baseStyles = "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none";
  
  const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 shadow-sm",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 active:bg-gray-400",
    outline: "border border-gray-300 bg-transparent hover:bg-gray-50 active:bg-gray-100",
    ghost: "bg-transparent hover:bg-gray-100 active:bg-gray-200",
    link: "bg-transparent underline-offset-4 hover:underline text-blue-600 hover:text-blue-700",
  };
  
  const sizeStyles = {
    sm: "text-xs px-3 py-1.5 rounded-md",
    md: "text-sm px-5 py-2.5 rounded-md",
    lg: "text-base px-7 py-3.5 rounded-lg font-semibold",
  };
  
  const widthStyles = fullWidth ? "w-full" : "";
  
  return (
    <button
      className={cn(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        widthStyles,
        isLoading && "relative text-transparent transition-none hover:text-transparent",
        "tracking-wide",
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <svg 
            className="animate-spin h-5 w-5 text-current" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
            />
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      )}
      <span className={cn(isLoading && "invisible")}>
        {children}
      </span>
    </button>
  );
} 