import React from 'react';
import { cn } from '@/utils/cn';

interface RadioOption {
  value: string;
  label: string;
  description?: string;
}

interface RadioGroupProps {
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  name: string;
  label?: string;
  error?: string;
  className?: string;
}

export function RadioGroup({
  options,
  value,
  onChange,
  name,
  label,
  error,
  className,
}: RadioGroupProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {label && (
        <label className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      
      <div className="space-y-2">
        {options.map((option) => (
          <div
            key={option.value}
            className={cn(
              "flex items-center p-3 rounded-md border cursor-pointer transition-colors",
              value === option.value 
                ? "border-blue-500 bg-blue-50" 
                : "border-gray-300 hover:bg-gray-50"
            )}
            onClick={() => onChange(option.value)}
          >
            <input
              type="radio"
              id={`${name}-${option.value}`}
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange(e.target.value)}
              className="sr-only" // Esconde o input nativo e usamos estilo customizado
            />
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "w-4 h-4 rounded-full border flex items-center justify-center",
                  value === option.value
                    ? "border-blue-500"
                    : "border-gray-300"
                )}
              >
                {value === option.value && (
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                )}
              </div>
              <div className="flex flex-col">
                <label
                  htmlFor={`${name}-${option.value}`}
                  className="font-medium text-gray-700 cursor-pointer"
                >
                  {option.label}
                </label>
                {option.description && (
                  <p className="text-sm text-gray-500">{option.description}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
} 