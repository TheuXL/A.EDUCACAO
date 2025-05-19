import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AnalyzeResponse } from '@/services/api';
import { validateMediaUrl } from '@/utils/mediaUtils';

interface Exercise {
  question: string;
  options?: string[];
  answer?: string;
  explanation?: string;
}

interface ExerciseContentProps {
  filePath: string;
}

export function ExerciseContent({ filePath }: ExerciseContentProps) {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState<boolean>(false);

  useEffect(() => {
    const fetchExercises = async () => {
      try {
        setLoading(true);
        
        // Constrói a URL completa usando o utilitário
        const fileUrl = validateMediaUrl(filePath);
        
        // Busca o conteúdo do arquivo
        const response = await fetch(fileUrl);
        
        if (!response.ok) {
          throw new Error(`Erro ao carregar exercícios (${response.status})`);
        }
        
        const content = await response.text();
        
        // Tenta analisar como JSON primeiro
        try {
          const jsonData = JSON.parse(content);
          
          // Verifica se é um array de exercícios
          if (Array.isArray(jsonData)) {
            setExercises(jsonData);
          } 
          // Verifica se tem uma propriedade exercises
          else if (jsonData.exercises && Array.isArray(jsonData.exercises)) {
            setExercises(jsonData.exercises);
          }
          // Caso contrário, tenta extrair exercícios do objeto
          else {
            const extractedExercises: Exercise[] = [];
            
            // Procura por propriedades que parecem ser exercícios
            Object.entries(jsonData).forEach(([key, value]) => {
              if (typeof value === 'object' && value !== null && 'question' in value) {
                extractedExercises.push(value as Exercise);
              }
            });
            
            if (extractedExercises.length > 0) {
              setExercises(extractedExercises);
            } else {
              throw new Error('Formato de exercícios não reconhecido');
            }
          }
        } 
        // Se não for JSON, tenta extrair exercícios do texto
        catch (jsonError) {
          // Extrai exercícios do texto formatado
          const textExercises = parseTextExercises(content);
          if (textExercises.length > 0) {
            setExercises(textExercises);
          } else {
            throw new Error('Não foi possível extrair exercícios do conteúdo');
          }
        }
        
        setError(null);
      } catch (err) {
        console.error('Erro ao carregar exercícios:', err);
        setError(err instanceof Error ? err.message : 'Erro desconhecido ao carregar exercícios');
        setExercises([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchExercises();
  }, [filePath]);
  
  // Função para extrair exercícios de texto formatado
  const parseTextExercises = (text: string): Exercise[] => {
    const exercises: Exercise[] = [];
    
    // Divide o texto em linhas
    const lines = text.split('\n');
    
    let currentExercise: Partial<Exercise> | null = null;
    let collectingOptions = false;
    let currentOptions: string[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Ignora linhas vazias
      if (!line) continue;
      
      // Verifica se é o início de um novo exercício (número seguido de ponto ou parêntese)
      const questionMatch = line.match(/^(\d+)[.)](.+)/);
      if (questionMatch) {
        // Se já estava coletando um exercício, salva o anterior
        if (currentExercise && currentExercise.question) {
          if (collectingOptions) {
            currentExercise.options = [...currentOptions];
            collectingOptions = false;
            currentOptions = [];
          }
          exercises.push(currentExercise as Exercise);
        }
        
        // Inicia um novo exercício
        currentExercise = {
          question: questionMatch[2].trim()
        };
        continue;
      }
      
      // Se não está coletando um exercício, continua
      if (!currentExercise) continue;
      
      // Verifica se é uma opção (a), b), c), etc. ou A., B., C., etc.)
      const optionMatch = line.match(/^[a-zA-Z][).] (.+)/);
      if (optionMatch) {
        if (!collectingOptions) {
          collectingOptions = true;
          currentOptions = [];
        }
        currentOptions.push(optionMatch[1].trim());
        continue;
      }
      
      // Verifica se é a resposta
      const answerMatch = line.match(/^(Resposta|Answer|Gabarito):\s*(.+)/i);
      if (answerMatch && currentExercise) {
        currentExercise.answer = answerMatch[2].trim();
        continue;
      }
      
      // Verifica se é uma explicação
      const explanationMatch = line.match(/^(Explicação|Explanation):\s*(.+)/i);
      if (explanationMatch && currentExercise) {
        currentExercise.explanation = explanationMatch[2].trim();
        continue;
      }
      
      // Se estamos dentro de um exercício e não é nenhum dos casos acima,
      // adiciona à pergunta atual (pode ser continuação da pergunta)
      if (currentExercise && !collectingOptions) {
        currentExercise.question += ' ' + line;
      }
    }
    
    // Adiciona o último exercício se existir
    if (currentExercise && currentExercise.question) {
      if (collectingOptions) {
        currentExercise.options = [...currentOptions];
      }
      exercises.push(currentExercise as Exercise);
    }
    
    return exercises;
  };
  
  const handleAnswerSelect = (exerciseIndex: number, answer: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [exerciseIndex]: answer
    }));
  };
  
  const handleSubmit = () => {
    setShowResults(true);
  };
  
  const handleReset = () => {
    setSelectedAnswers({});
    setShowResults(false);
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Carregando exercícios...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <p>Erro ao carregar exercícios: {error}</p>
        <p className="mt-2 text-sm">
          Tente acessar diretamente o arquivo: 
          <a 
            href={validateMediaUrl(filePath)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 underline ml-1"
          >
            Abrir arquivo
          </a>
        </p>
      </div>
    );
  }
  
  if (exercises.length === 0) {
          return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        <p>Nenhum exercício encontrado no arquivo.</p>
            </div>
          );
        }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-800">Exercícios</h3>
        <p className="text-sm text-gray-500">Responda às questões abaixo para testar seus conhecimentos</p>
        </div>
        
      <div className="p-4">
        {exercises.map((exercise, index) => (
          <div key={index} className={`mb-6 pb-4 ${index < exercises.length - 1 ? 'border-b border-gray-200' : ''}`}>
            <p className="font-medium mb-3">
              <span className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 inline-flex items-center justify-center mr-2">
                {index + 1}
              </span>
              {exercise.question}
            </p>
            
            {exercise.options && (
              <div className="ml-8 space-y-2">
                {exercise.options.map((option, optionIndex) => (
                  <label 
                    key={optionIndex} 
                    className={`flex items-start p-2 rounded-md cursor-pointer ${
                      selectedAnswers[index] === option 
                        ? showResults 
                          ? exercise.answer === option 
                            ? 'bg-green-50 border border-green-200' 
                            : 'bg-red-50 border border-red-200'
                          : 'bg-blue-50 border border-blue-200' 
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`exercise-${index}`}
                      value={option}
                      checked={selectedAnswers[index] === option}
                      onChange={() => handleAnswerSelect(index, option)}
                      disabled={showResults}
                      className="mt-0.5"
                    />
                    <span className="ml-2">{option}</span>
                    {showResults && selectedAnswers[index] === option && exercise.answer === option && (
                      <span className="ml-2 text-green-600">✓</span>
                    )}
                    {showResults && selectedAnswers[index] === option && exercise.answer !== option && (
                      <span className="ml-2 text-red-600">✗</span>
                    )}
                  </label>
                ))}
          </div>
            )}
            
            {showResults && exercise.explanation && (
              <div className="mt-3 ml-8 p-3 bg-blue-50 rounded-md text-sm">
                <p className="font-medium text-blue-800">Explicação:</p>
                <p className="text-gray-800">{exercise.explanation}</p>
              </div>
            )}
            
            {showResults && exercise.answer && !exercise.options && (
              <div className="mt-3 ml-8 p-3 bg-blue-50 rounded-md text-sm">
                <p className="font-medium text-blue-800">Resposta:</p>
                <p className="text-gray-800">{exercise.answer}</p>
            </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="p-4 border-t border-gray-200 flex justify-end">
        {!showResults ? (
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            disabled={Object.keys(selectedAnswers).length === 0}
          >
            Verificar respostas
          </button>
        ) : (
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Tentar novamente
          </button>
        )}
      </div>
    </div>
  );
}

export default ExerciseContent; 