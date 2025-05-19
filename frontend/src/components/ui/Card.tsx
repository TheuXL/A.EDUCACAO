import React from 'react';
import { cn } from '@/utils/cn';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow overflow-hidden",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

function CardHeader({ className, children }: CardHeaderProps) {
  return (
    <div
      className={cn(
        "px-6 py-5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50",
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

function CardContent({ className, children }: CardContentProps) {
  return (
    <div
      className={cn(
        "px-6 py-6 space-y-4",
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

function CardFooter({ className, children }: CardFooterProps) {
  return (
    <div
      className={cn(
        "px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700",
        className
      )}
    >
      {children}
    </div>
  );
}

Card.Header = CardHeader;
Card.Content = CardContent;
Card.Footer = CardFooter;

export { CardHeader, CardContent, CardFooter }; 