import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { analyzeQuery, AnalyzeResponse, generateExercises } from '@/services/api';
import { AdaptiveResponse } from './AdaptiveResponse';
import { ExerciseContent } from './ExerciseContent';
import { validateMediaUrl } from '@/utils/mediaUtils';

interface AdaptiveLearningContentProps {
  userId: string;
  knowledgeGaps: string[];
  preferredFormat: string;
  level: string;
}

export function AdaptiveLearningContent({
  userId,
  knowledgeGaps,
  preferredFormat,
  level
}: AdaptiveLearningContentProps) {
  const [currentGapIndex, setCurrentGapIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedbackStatus, setFeedbackStatus] = useState<'pending' | 'submitted' | null>(null);
  const [exerciseMode, setExerciseMode] = useState(false);
  const [exerciseCompleted, setExerciseCompleted] = useState(false);
  const [exerciseCorrect, setExerciseCorrect] = useState(false);

  // Buscar conteúdo adaptativo com base na lacuna atual
  useEffect(() => {
    if (knowledgeGaps.length > 0) {
      fetchAdaptiveContent();
    }
  }, [currentGapIndex, exerciseMode]);

  const fetchAdaptiveContent = async () => {
    if (knowledgeGaps.length === 0) {
      setError('Nenhuma área de desenvolvimento identificada.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setFeedbackStatus('pending');
    setExerciseCompleted(false);

    try {
      const currentGap = knowledgeGaps[currentGapIndex];
      
      let result;
      
      // Monta a consulta com base no modo (conteúdo ou exercício)
      if (exerciseMode) {
        // Usa a função específica para gerar exercícios
        result = await generateExercises(
          currentGap,
          level,
          preferredFormat
        );
      } else {
        // Usa a função normal para explicações
        result = await analyzeQuery({
          query: `Explique ${currentGap} para nível ${level}`,
          user_level: level,
          preferred_format: preferredFormat,
          user_id: userId,
          use_neural_network: true
        });
      }

      // Verifica se a resposta é válida
      if (!result || !result.response) {
        setError("A API retornou uma resposta vazia ou inválida. Por favor, tente novamente.");
        console.error("Resposta vazia ou inválida:", result);
        return;
      }

      // Salva a resposta
      setResponse(result);
    } catch (err) {
      console.error("Erro ao buscar conteúdo adaptativo:", err);
      setError(`Ocorreu um erro ao processar sua consulta: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (feedback: 'positive' | 'negative') => {
    console.log(`Feedback ${feedback} enviado`);
    setFeedbackStatus('submitted');
  };

  const handleSelectRelatedContent = (content: any) => {
    console.log("Conteúdo selecionado:", content);
  };

  const handleSelectSuggestion = (suggestion: string) => {
    console.log("Sugestão selecionada:", suggestion);
  };
  
  const handleExerciseComplete = (isCorrect: boolean) => {
    setExerciseCompleted(true);
    setExerciseCorrect(isCorrect);
  };

  const navigateToNextGap = () => {
    if (currentGapIndex < knowledgeGaps.length - 1) {
      setCurrentGapIndex(currentGapIndex + 1);
      setExerciseMode(false);
    }
  };

  const navigateToPreviousGap = () => {
    if (currentGapIndex > 0) {
      setCurrentGapIndex(currentGapIndex - 1);
      setExerciseMode(false);
    }
  };

  const toggleMode = () => {
    setExerciseMode(!exerciseMode);
  };

  // Renderiza o título do conteúdo atual
  const renderContentTitle = () => {
    if (knowledgeGaps.length === 0) return 'Conteúdo Personalizado';
    
    const currentGap = knowledgeGaps[currentGapIndex];
    return exerciseMode 
      ? `Exercício: ${currentGap}` 
      : `Conteúdo: ${currentGap}`;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">{renderContentTitle()}</h2>
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={toggleMode}
            >
              {exerciseMode ? 'Ver Conteúdo' : 'Ver Exercícios'}
            </Button>
          </div>
        </div>
        <p className="text-sm text-gray-600">
          Conteúdo personalizado no formato {preferredFormat} para nível {level}
        </p>
      </CardHeader>
      
      <CardContent>
        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg">
            <div className="font-medium mb-2">
              {error}
            </div>
            <Button 
              onClick={fetchAdaptiveContent}
              variant="outline" 
              size="sm"
              className="text-sm px-3 py-1 bg-red-100 hover:bg-red-200 rounded transition-colors"
            >
              Tentar novamente
            </Button>
          </div>
        )}
        
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <p className="text-gray-600">Carregando conteúdo personalizado...</p>
          </div>
        ) : response ? (
          <div className="mt-4">
            {exerciseMode ? (
              <ExerciseContent
                filePath={response.file_path || 'text/Exercícios.txt'}
              />
            ) : (
              <AdaptiveResponse 
                data={response} 
                onFeedback={handleFeedback}
                onSelectRelatedContent={handleSelectRelatedContent}
                feedbackStatus={feedbackStatus}
                onSelectSuggestion={handleSelectSuggestion}
              />
            )}
            
            {exerciseMode && exerciseCompleted && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                <div className="flex items-center mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="font-medium text-blue-800">Resultado do Exercício</h3>
                </div>
                <p className="text-blue-700 mb-3">
                  {exerciseCorrect 
                    ? 'Parabéns! Você acertou o exercício. Continue praticando para reforçar seu aprendizado.'
                    : 'Não desanime! A prática leva à perfeição. Revise o conteúdo e tente novamente.'}
                </p>
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setExerciseMode(false);
                      setExerciseCompleted(false);
                    }}
                  >
                    Voltar ao Conteúdo
                  </Button>
                </div>
              </div>
            )}
            
            {knowledgeGaps.length > 1 && (
              <div className="flex justify-between mt-6">
                <Button
                  variant="outline"
                  onClick={navigateToPreviousGap}
                  disabled={currentGapIndex === 0}
                >
                  Tópico Anterior
                </Button>
                
                <Button
                  variant="primary"
                  onClick={navigateToNextGap}
                  disabled={currentGapIndex === knowledgeGaps.length - 1}
                >
                  Próximo Tópico
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">Nenhum conteúdo carregado.</p>
            <Button
              variant="primary"
              onClick={fetchAdaptiveContent}
            >
              Carregar Conteúdo
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 