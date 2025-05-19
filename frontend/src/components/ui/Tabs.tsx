import React from 'react';
import { cn } from '@/utils/cn';

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div className={cn("border-b border-gray-200", className)}>
      <nav className="flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          
          return (
            <button
              key={tab.id}
              className={cn(
                "py-4 px-1 text-sm font-medium border-b-2 -mb-px",
                isActive
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
              onClick={() => onChange(tab.id)}
              aria-current={isActive ? "page" : undefined}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
} 