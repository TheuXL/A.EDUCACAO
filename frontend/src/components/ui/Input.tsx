import React, { forwardRef } from 'react';
import { cn } from '@/utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, fullWidth = false, helperText, id, ...props }, ref) => {
    // Generate a unique ID if not provided
    const inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;
    
    return (
      <div className={cn("flex flex-col space-y-2", fullWidth ? "w-full" : "")}>
        {label && (
          <label 
            htmlFor={inputId}
            className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          <input
            id={inputId}
            className={cn(
              "flex h-11 w-full rounded-md border border-gray-300 bg-white px-4 py-2.5 text-base placeholder:text-gray-400",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-100",
              error ? "border-red-500 focus:ring-red-500 focus:border-red-500" : "",
              fullWidth ? "w-full" : "",
              className
            )}
            ref={ref}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-description` : undefined}
            {...props}
          />
        </div>
        
        {error && (
          <p 
            id={`${inputId}-error`}
            className="text-sm text-red-600 dark:text-red-500 mt-1"
          >
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p 
            id={`${inputId}-description`}
            className="text-sm text-gray-500 dark:text-gray-400 mt-1"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input'; 