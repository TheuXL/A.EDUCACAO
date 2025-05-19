'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { SearchForm, SearchFormData } from '@/components/forms/SearchForm';
import { analyzeQuery, AnalyzeResponse, RelatedContent } from '@/services/api';
import { AdaptiveResponse } from '@/components/content/AdaptiveResponse';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [responses, setResponses] = useState<AnalyzeResponse[]>([]);
  const [queries, setQueries] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [feedbackStatus, setFeedbackStatus] = useState<Record<string, 'pending' | 'submitted' | null>>({});

  const handleSearch = async (data: SearchFormData) => {
    setIsLoading(true);
    setError(null);
    
    // Adicionar a consulta do usuário à lista
    setQueries(prev => [...prev, data.query]);
    
    try {
      // Se temos um userId da busca anterior, reuse-o
      const userIdToUse = userId || undefined;
      
      // Envia a requisição para a API
      const result = await analyzeQuery({
        query: data.query,
        user_level: data.level,
        preferred_format: data.format,
        user_id: userIdToUse,
        use_neural_network: data.useNeural
      });
      
      // Verifica se a resposta é válida
      if (!result || !result.response) {
        setError("A API retornou uma resposta vazia ou inválida. Por favor, tente novamente.");
        console.error("Resposta vazia ou inválida:", result);
        return;
      }
      
      // Salva a resposta e o ID do usuário
      setResponses(prev => [...prev, result]);
      setFeedbackStatus(prev => ({
        ...prev,
        [result.query_id || Date.now().toString()]: 'pending'
      }));
      
      if (result.user_id) {
        setUserId(result.user_id);
      }
    } catch (err) {
      console.error("Erro ao buscar:", err);
      setError(`Ocorreu um erro ao processar sua consulta: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (feedback: 'positive' | 'negative', responseId: string) => {
    console.log(`Feedback ${feedback} enviado para resposta ${responseId}`);
    setFeedbackStatus(prev => ({
      ...prev,
      [responseId]: 'submitted'
    }));
  };

  const handleSelectRelatedContent = (content: RelatedContent) => {
    console.log("Conteúdo selecionado:", content);
    // Aqui você pode implementar a lógica para exibir o conteúdo relacionado
  };

  const handleSelectSuggestion = (suggestion: string) => {
    console.log("Sugestão selecionada:", suggestion);
    handleSearch({
      query: suggestion,
      format: 'texto',
      level: 'intermediário',
      useNeural: true
    });
  };

  const clearChat = () => {
    setResponses([]);
    setQueries([]);
    setFeedbackStatus({});
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
              A
            </div>
            <h1 className="text-lg font-bold">A.Educação</h1>
          </div>
        </div>
        
        {/* New Chat Button */}
        <div className="p-3">
          <Button 
            onClick={clearChat}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white border border-gray-600 rounded-md flex items-center justify-center py-3"
          >
            Nova conversa
          </Button>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3">
          <div className="space-y-1">
            <Link href="/" className="flex items-center px-3 py-2 text-sm rounded-md bg-gray-800 text-white">
              Início
            </Link>
            <Link href="/learning" className="flex items-center px-3 py-2 text-sm rounded-md text-gray-300 hover:bg-gray-800 hover:text-white">
              Aprendizado
            </Link>
            <Link href="/admin" className="flex items-center px-3 py-2 text-sm rounded-md text-gray-300 hover:bg-gray-800 hover:text-white">
              Admin
            </Link>
          </div>
        </nav>
        
        {/* User info */}
        <div className="p-3 border-t border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
              Usuário
            </div>
            <div className="text-sm">
              <p className="text-gray-300">Usuário</p>
              <p className="text-gray-500 text-xs">{userId || 'Anônimo'}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto">
          {queries.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                  A
                </div>
              </div>
              <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">A.Educação</h2>
              <p className="text-gray-600 dark:text-gray-400 text-center max-w-md mb-8">
                Plataforma de aprendizagem adaptativa que personaliza o conteúdo de acordo com suas necessidades.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-lg">
                <Button 
                  onClick={() => handleSearch({
                    query: "O que é HTML e para que serve?",
                    format: "texto",
                    level: "iniciante",
                    useNeural: true
                  })}
                  variant="outline"
                  className="text-left px-4 py-3 h-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span className="flex flex-col">
                    <span className="font-medium">O que é HTML?</span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">Explicação para iniciantes</span>
                  </span>
                </Button>
                <Button 
                  onClick={() => handleSearch({
                    query: "Explique os conceitos de CSS Grid e Flexbox",
                    format: "texto",
                    level: "intermediário",
                    useNeural: true
                  })}
                  variant="outline"
                  className="text-left px-4 py-3 h-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span className="flex flex-col">
                    <span className="font-medium">CSS Grid vs Flexbox</span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">Comparação detalhada</span>
                  </span>
                </Button>
                <Button 
                  onClick={() => handleSearch({
                    query: "Como usar JavaScript para manipular o DOM?",
                    format: "vídeo",
                    level: "intermediário",
                    useNeural: true
                  })}
                  variant="outline"
                  className="text-left px-4 py-3 h-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span className="flex flex-col">
                    <span className="font-medium">Manipulação do DOM</span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">Com exemplos em vídeo</span>
                  </span>
                </Button>
                <Button 
                  onClick={() => handleSearch({
                    query: "Explique o conceito de React Hooks",
                    format: "texto",
                    level: "avançado",
                    useNeural: true
                  })}
                  variant="outline"
                  className="text-left px-4 py-3 h-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span className="flex flex-col">
                    <span className="font-medium">React Hooks</span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">Explicação avançada</span>
                  </span>
                </Button>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto w-full py-6">
              {queries.map((query, index) => (
                <div key={`conversation-${index}`} className="mb-8">
                  {/* User query */}
                  <div className="flex items-start mb-6 px-4">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold mr-3 flex-shrink-0">
                      U
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-lg px-4 py-3 max-w-3xl w-full shadow-sm">
                      <p className="text-gray-800 dark:text-gray-200">{query}</p>
                    </div>
                  </div>
                  
                  {/* System response */}
                  {responses[index] && (
                    <div className="flex items-start px-4">
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold mr-3 flex-shrink-0">
                        A
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg px-4 py-3 max-w-3xl w-full shadow-sm">
                        <AdaptiveResponse 
                          data={responses[index]} 
                          onFeedback={(feedback) => handleFeedback(feedback, responses[index].query_id || String(index))}
                          onSelectRelatedContent={handleSelectRelatedContent}
                          feedbackStatus={feedbackStatus[responses[index].query_id || String(index)]}
                          onSelectSuggestion={handleSelectSuggestion}
                        />
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              {error && (
                <div className="flex items-start px-4 mb-6">
                  <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-semibold mr-3 flex-shrink-0">
                    !
                  </div>
                  <div className="bg-red-50 dark:bg-red-900 text-red-700 dark:text-red-200 rounded-lg px-4 py-3 max-w-3xl w-full">
                    <p>{error}</p>
                    <button 
                      onClick={() => setError(null)}
                      className="text-sm px-3 py-1 mt-2 bg-red-100 dark:bg-red-800 hover:bg-red-200 dark:hover:bg-red-700 rounded transition-colors"
                    >
                      Tentar novamente
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
          <div className="max-w-3xl mx-auto">
            <SearchForm 
              onSubmit={handleSearch} 
              isLoading={isLoading} 
              inDialogMode={true} 
            />
            <div className="text-center mt-2 text-xs text-gray-500 dark:text-gray-400">
              A.Educação pode produzir informações incorretas. Verifique fatos importantes.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
