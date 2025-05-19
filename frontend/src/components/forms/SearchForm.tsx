import React, { useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { RadioGroup } from '@/components/ui/RadioGroup';
import { Select } from '../ui/Select';

export interface SearchFormData {
  query: string;
  format: string;
  level: string;
  useNeural: boolean;
  conversationId?: string;
}

interface SearchFormProps {
  onSubmit: (data: SearchFormData) => void;
  isLoading?: boolean;
  conversationId?: string;
  inDialogMode?: boolean;
}

export function SearchForm({ onSubmit, isLoading = false, conversationId, inDialogMode = false }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [format, setFormat] = useState('texto');
  const [level, setLevel] = useState('intermediário');
  const [useNeural, setUseNeural] = useState(true);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    onSubmit({
      query,
      format,
      level,
      useNeural,
      conversationId
    });
    
    // Limpar o campo de consulta se estiver em modo de diálogo
    if (inDialogMode) {
      setQuery('');
    }
  };
  
  const formatOptions = [
    {
      value: 'texto',
      label: 'Texto',
      description: 'Artigos, documentos e conteúdos escritos'
    },
    {
      value: 'vídeo',
      label: 'Vídeo',
      description: 'Aulas, tutoriais e demonstrações em vídeo'
    },
    {
      value: 'imagem',
      label: 'Imagem',
      description: 'Infográficos, diagramas e ilustrações explicativas'
    },
    {
      value: 'áudio',
      label: 'Áudio',
      description: 'Podcasts, audiobooks e conteúdos em áudio'
    }
  ];
  
  const levelOptions = [
    {
      value: 'iniciante',
      label: 'Iniciante',
      description: 'Explicações mais detalhadas e simplificadas'
    },
    {
      value: 'intermediário',
      label: 'Intermediário',
      description: 'Equilíbrio entre conceitos básicos e avançados'
    },
    {
      value: 'avançado',
      label: 'Avançado',
      description: 'Conteúdo aprofundado com termos técnicos'
    }
  ];
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {!inDialogMode && (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 hover:border-blue-300 dark:hover:border-blue-500 transition-all duration-200">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Formato preferido</label>
              <Select
                options={[
                  { value: 'texto', label: 'Texto' },
                  { value: 'vídeo', label: 'Vídeo' },
                  { value: 'imagem', label: 'Imagem' },
                  { value: 'áudio', label: 'Áudio' }
                ]}
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full border-gray-200 dark:border-gray-700 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-200"
              />
            </div>
            
            <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 hover:border-blue-300 dark:hover:border-blue-500 transition-all duration-200">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nível de conhecimento</label>
              <Select
                options={[
                  { value: 'iniciante', label: 'Iniciante' },
                  { value: 'intermediário', label: 'Intermediário' },
                  { value: 'avançado', label: 'Avançado' }
                ]}
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="w-full border-gray-200 dark:border-gray-700 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-200"
              />
            </div>
            
            <div className="flex items-end">
              <Button 
                type="submit" 
                disabled={isLoading || !query.trim()}
                fullWidth
                className="bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Consultando...
                  </div>
                ) : 'Consultar'}
              </Button>
            </div>
          </div>
          
          <div className="flex items-center mt-4 bg-blue-50 dark:bg-gray-700 p-2 rounded-lg">
            <input
              type="checkbox"
              id="useNeural"
              checked={useNeural}
              onChange={() => setUseNeural(!useNeural)}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-600 focus:ring-blue-500"
            />
            <label htmlFor="useNeural" className="ml-2 text-sm text-gray-700 dark:text-gray-300 flex items-center">
              <span className="mr-1">Usar IA Adaptativa para personalizar resultados</span>
              <span className="ml-1 text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">Recomendado</span>
            </label>
          </div>
        </div>
      )}
      
      {inDialogMode && (
        <div className="relative rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700 shadow-sm">
          <div className="flex items-end">
            <div className="flex-grow">
              <textarea
                placeholder="Envie uma mensagem..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full resize-none border-0 bg-transparent py-3 px-4 focus:ring-0 focus-visible:ring-0 outline-none text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
                rows={1}
                style={{ minHeight: '56px', maxHeight: '200px' }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
                }}
              />
            </div>
            <div className="pr-2 pb-2">
              <Button 
                type="submit" 
                disabled={isLoading || !query.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
              >
                {isLoading ? (
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
                  </svg>
                )}
              </Button>
            </div>
          </div>
          <div className="absolute bottom-1 left-0 right-0 hidden sm:flex justify-center">
            <div className="flex space-x-1 text-xs text-gray-500 dark:text-gray-400">
              <span>Formato: {formatOptions.find(opt => opt.value === format)?.label}</span>
              <span>•</span>
              <span>Nível: {levelOptions.find(opt => opt.value === level)?.label}</span>
            </div>
          </div>
        </div>
      )}
    </form>
  );
} 