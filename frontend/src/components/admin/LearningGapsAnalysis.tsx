import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import api from '@/services/api';

interface GapAnalysisResult {
  user_id: string;
  status: string;
  analysis_date?: string;
  overall_progress?: number;
  engagement_metrics?: Record<string, any>;
  identified_gaps: Array<{
    topic: string;
    severity: string;
    confidence: number;
    suggestions?: string[];
  }>;
  improvement_suggestions?: Array<{
    resource_type: string;
    title: string;
    description: string;
    difficulty: string;
  }>;
  strengths: string[];
  weaknesses: string[];
  message?: string;
}

export function LearningGapsAnalysis() {
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState('');
  const [results, setResults] = useState<GapAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async () => {
    if (!userId.trim()) {
      setError('ID do usuário é obrigatório');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get<GapAnalysisResult>(`/api/learning/analysis/${userId}`);
      setResults(response.data);
    } catch (err: any) {
      setError(err.message || 'Erro ao analisar lacunas de aprendizado');
      console.error('Erro na análise de lacunas:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const updateUserProfile = async () => {
    if (!userId.trim()) {
      setError('ID do usuário é obrigatório');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/api/learning/update-profile', { user_id: userId });
      
      if (response.data.status === 'success') {
        // Recarregar os resultados da análise após a atualização
        const updatedAnalysis = await api.get<GapAnalysisResult>(`/api/learning/analysis/${userId}`);
        setResults(updatedAnalysis.data);
      } else {
        setError(response.data.message || 'Erro ao atualizar perfil');
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao atualizar perfil do usuário');
      console.error('Erro na atualização do perfil:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'alta': return 'bg-red-100 text-red-800';
      case 'média': return 'bg-yellow-100 text-yellow-800';
      case 'baixa': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <h2 className="text-xl font-bold">Análise de Lacunas de Aprendizado</h2>
        <p className="text-sm text-gray-600">Identifique lacunas de conhecimento e oportunidades de melhoria para estudantes</p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex gap-4">
          <Input
            label="ID do Usuário"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Informe o ID do usuário"
            className="flex-grow"
          />
          
          <div className="flex items-end gap-2">
            <Button
              onClick={runAnalysis}
              isLoading={isLoading}
              variant="primary"
            >
              Analisar
            </Button>
            
            <Button
              onClick={updateUserProfile}
              isLoading={isLoading}
              variant="outline"
              disabled={!userId.trim()}
            >
              Atualizar Perfil
            </Button>
          </div>
        </div>
        
        {error && (
          <div className="p-3 bg-red-100 text-red-800 rounded-md">
            {error}
          </div>
        )}
        
        {results && (
          <div className="space-y-6 mt-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Resultados da Análise</h3>
              {results.analysis_date && (
                <span className="text-sm text-gray-500">
                  Análise realizada em: {new Date(results.analysis_date).toLocaleString()}
                </span>
              )}
            </div>
            
            {results.overall_progress !== undefined && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Progresso Geral</h4>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full" 
                    style={{ width: `${results.overall_progress * 100}%` }}
                  ></div>
                </div>
                <p className="text-sm mt-2 text-gray-700">
                  {(results.overall_progress * 100).toFixed(1)}% de aproveitamento
                </p>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Pontos Fortes</h4>
                {results.strengths.length > 0 ? (
                  <ul className="space-y-1">
                    {results.strengths.map((strength, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <span className="text-green-500">✓</span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">Nenhum ponto forte identificado</p>
                )}
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Pontos Fracos</h4>
                {results.weaknesses.length > 0 ? (
                  <ul className="space-y-1">
                    {results.weaknesses.map((weakness, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <span className="text-red-500">✗</span>
                        {weakness}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">Nenhum ponto fraco identificado</p>
                )}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-3">Lacunas de Conhecimento Identificadas</h4>
              {results.identified_gaps.length > 0 ? (
                <div className="space-y-2">
                  {results.identified_gaps.map((gap, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                      <div className="flex justify-between items-center mb-2">
                        <h5 className="font-medium">{gap.topic}</h5>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getSeverityColor(gap.severity)}`}>
                          Severidade: {gap.severity}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        Confiança: {(gap.confidence * 100).toFixed(0)}%
                      </p>
                      {gap.suggestions && gap.suggestions.length > 0 && (
                        <div className="mt-2">
                          <h6 className="text-xs font-medium text-gray-700">Sugestões:</h6>
                          <ul className="list-disc list-inside text-xs pl-2 mt-1 text-gray-600">
                            {gap.suggestions.map((suggestion, idx) => (
                              <li key={idx}>{suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Nenhuma lacuna de conhecimento identificada</p>
              )}
            </div>
            
            {results.improvement_suggestions && results.improvement_suggestions.length > 0 && (
              <div>
                <h4 className="font-medium mb-3">Sugestões de Melhoria</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {results.improvement_suggestions.map((suggestion, index) => (
                    <div key={index} className="p-3 bg-blue-50 rounded-md border border-blue-200">
                      <h5 className="font-medium text-blue-800">{suggestion.title}</h5>
                      <p className="text-sm text-gray-700 my-1">{suggestion.description}</p>
                      <div className="flex justify-between items-center mt-2 text-xs">
                        <span className="bg-blue-100 px-2 py-0.5 rounded-full text-blue-800">
                          {suggestion.resource_type}
                        </span>
                        <span className="text-gray-500">
                          Dificuldade: {suggestion.difficulty}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
} 