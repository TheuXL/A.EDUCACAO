import React from 'react';
import { cn } from '@/utils/cn';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, label, error, fullWidth = false, ...props }, ref) => {
    return (
      <div className={cn("flex flex-col gap-1.5", fullWidth ? "w-full" : "")}>
        {label && (
          <label 
            htmlFor={props.id} 
            className="text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        <select
          className={cn(
            "px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm appearance-none text-gray-900",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
            error ? "border-red-500" : "",
            className
          )}
          ref={ref}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value} className="text-gray-900">
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export { Select }; 