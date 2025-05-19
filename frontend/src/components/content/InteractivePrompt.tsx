import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { RadioGroup } from '@/components/ui/RadioGroup';
import { analyzeQuery, AnalyzeResponse } from '@/services/api';

interface InteractivePromptProps {
  userId?: string;
  onComplete?: (data: {
    userId: string;
    knowledgeGaps: string[];
    preferredFormat: string;
    level: string;
  }) => void;
}

interface Question {
  id: number;
  text: string;
  type: 'multiple-choice' | 'open-ended';
  options?: { value: string; label: string }[];
  answer?: string;
  userResponse?: string;
  isCorrect?: boolean;
}

export function InteractivePrompt({ userId: initialUserId, onComplete }: InteractivePromptProps) {
  const [userId, setUserId] = useState<string>(initialUserId || '');
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AnalyzeResponse | null>(null);
  const [knowledgeGaps, setKnowledgeGaps] = useState<string[]>([]);
  const [preferredFormat, setPreferredFormat] = useState<string>('texto');
  const [userLevel, setUserLevel] = useState<string>('intermediário');
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [userInput, setUserInput] = useState<string>('');
  const [formatPreferences, setFormatPreferences] = useState<Record<string, number>>({
    texto: 0,
    vídeo: 0,
    áudio: 0,
    imagem: 0
  });
  const [assessmentComplete, setAssessmentComplete] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Tópicos para avaliação - poderiam vir de uma API em um cenário real
  const topics = [
    'HTML',
    'CSS',
    'JavaScript',
    'Acessibilidade Web',
    'Responsividade'
  ];

  // Inicializa o processo de avaliação
  useEffect(() => {
    if (currentStep === 0 && userId) {
      generateInitialQuestions();
    }
  }, [userId, currentStep]);

  // Gera perguntas iniciais para avaliar o conhecimento
  const generateInitialQuestions = async () => {
    try {
      const generatedQuestions = topics.map((topic, index) => ({
        id: index + 1,
        text: `Qual é seu nível de conhecimento em ${topic}?`,
        type: 'multiple-choice' as const,
        options: [
          { value: 'iniciante', label: 'Iniciante - Conheço pouco ou nada' },
          { value: 'intermediário', label: 'Intermediário - Tenho conhecimento básico' },
          { value: 'avançado', label: 'Avançado - Tenho bom domínio' }
        ]
      }));

      // Adiciona perguntas sobre preferência de formato
      generatedQuestions.push({
        id: topics.length + 1,
        text: 'Qual formato você prefere para aprender novos conteúdos?',
        type: 'multiple-choice',
        options: [
          { value: 'texto', label: 'Texto - Artigos e documentação escrita' },
          { value: 'vídeo', label: 'Vídeo - Aulas e tutoriais em vídeo' },
          { value: 'áudio', label: 'Áudio - Podcasts e explicações em áudio' },
          { value: 'imagem', label: 'Imagem - Infográficos e diagramas' }
        ]
      });

      // Adiciona perguntas específicas para avaliar conhecimento
      const knowledgeQuestions = [
        {
          id: topics.length + 2,
          text: 'O que é HTML e qual sua função no desenvolvimento web?',
          type: 'open-ended' as const
        },
        {
          id: topics.length + 3,
          text: 'Descreva brevemente a estrutura básica de uma página HTML.',
          type: 'open-ended' as const
        }
      ];

      setQuestions([...generatedQuestions, ...knowledgeQuestions]);
      setCurrentQuestion(generatedQuestions[0]);
      setCurrentStep(1);
    } catch (err) {
      console.error('Erro ao gerar perguntas:', err);
      setError('Não foi possível iniciar a avaliação. Tente novamente.');
    }
  };

  // Processa a resposta do usuário e avança para a próxima pergunta
  const handleAnswer = async (answer: string) => {
    if (!currentQuestion) return;

    // Atualiza a resposta atual
    const updatedQuestion = { ...currentQuestion, userResponse: answer };
    
    // Atualiza a lista de perguntas
    const updatedQuestions = questions.map(q => 
      q.id === currentQuestion.id ? updatedQuestion : q
    );
    setQuestions(updatedQuestions);

    // Atualiza preferências de formato se for a pergunta sobre formato
    if (currentQuestion.text.includes('formato você prefere')) {
      setPreferredFormat(answer);
      setFormatPreferences(prev => ({
        ...prev,
        [answer]: prev[answer] + 1
      }));
    }

    // Se for uma pergunta sobre nível de conhecimento em um tópico específico
    if (currentQuestion.text.includes('nível de conhecimento em')) {
      const topic = currentQuestion.text.split('em ')[1].replace('?', '');
      if (answer === 'iniciante') {
        setKnowledgeGaps(prev => [...prev, topic]);
      }
      
      // Atualiza o nível geral do usuário com base nas respostas
      updateUserLevel(updatedQuestions);
    }

    // Avança para a próxima pergunta ou finaliza
    const nextQuestionIndex = questions.findIndex(q => q.id === currentQuestion.id) + 1;
    if (nextQuestionIndex < questions.length) {
      setCurrentQuestion(questions[nextQuestionIndex]);
      setUserInput('');
    } else {
      // Finaliza o processo de avaliação
      completeAssessment(updatedQuestions);
    }
  };

  // Atualiza o nível geral do usuário com base nas respostas
  const updateUserLevel = (updatedQuestions: Question[]) => {
    const levelQuestions = updatedQuestions.filter(q => 
      q.userResponse && 
      (q.userResponse === 'iniciante' || q.userResponse === 'intermediário' || q.userResponse === 'avançado')
    );
    
    if (levelQuestions.length > 0) {
      const levels = {
        'iniciante': 0,
        'intermediário': 0,
        'avançado': 0
      };
      
      levelQuestions.forEach(q => {
        if (q.userResponse) {
          levels[q.userResponse as keyof typeof levels]++;
        }
      });
      
      // Determina o nível predominante
      let maxLevel = 'intermediário';
      let maxCount = 0;
      
      Object.entries(levels).forEach(([level, count]) => {
        if (count > maxCount) {
          maxCount = count;
          maxLevel = level;
        }
      });
      
      setUserLevel(maxLevel);
    }
  };

  // Finaliza o processo de avaliação
  const completeAssessment = async (finalQuestions: Question[]) => {
    setIsLoading(true);
    
    try {
      // Analisa as respostas abertas para identificar lacunas de conhecimento
      const openEndedQuestions = finalQuestions.filter(q => q.type === 'open-ended' && q.userResponse);
      
      for (const question of openEndedQuestions) {
        if (!question.userResponse) continue;
        
        // Usa o serviço de análise para avaliar a resposta
        const analysisResult = await analyzeQuery({
          query: `Avalie esta resposta para a pergunta "${question.text}": "${question.userResponse}"`,
          user_level: userLevel,
          preferred_format: preferredFormat,
          user_id: userId
        });
        
        // Verifica se a resposta indica uma lacuna de conhecimento
        if (analysisResult.response.toLowerCase().includes('incorreto') || 
            analysisResult.response.toLowerCase().includes('incompleto')) {
          
          // Extrai o tópico da pergunta
          let topic = '';
          if (question.text.includes('HTML')) topic = 'HTML';
          else if (question.text.includes('CSS')) topic = 'CSS';
          else if (question.text.includes('JavaScript')) topic = 'JavaScript';
          else topic = 'Desenvolvimento Web';
          
          if (!knowledgeGaps.includes(topic)) {
            setKnowledgeGaps(prev => [...prev, topic]);
          }
        }
      }
      
      // Marca a avaliação como concluída
      setAssessmentComplete(true);
      
      // Chama o callback de conclusão se fornecido
      if (onComplete) {
        onComplete({
          userId,
          knowledgeGaps,
          preferredFormat,
          level: userLevel
        });
      }
      
    } catch (err) {
      console.error('Erro ao analisar respostas:', err);
      setError('Ocorreu um erro ao processar suas respostas. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  // Inicia o processo de avaliação
  const startAssessment = () => {
    if (!userId.trim()) {
      setError('Por favor, informe um ID de usuário para continuar.');
      return;
    }
    
    setError(null);
    generateInitialQuestions();
  };

  // Renderiza a tela inicial
  const renderInitialScreen = () => (
    <div className="text-center space-y-6">
      <h3 className="text-xl font-semibold text-gray-800">Avaliação Interativa de Conhecimento</h3>
      <p className="text-gray-600">
        Vamos identificar suas áreas de interesse e oportunidades de aprendizado.
        Esta avaliação ajudará a personalizar seu conteúdo educacional.
      </p>
      
      <div className="max-w-md mx-auto">
        <Input
          label="ID do Usuário"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="Digite seu ID de usuário"
          className="mb-4"
        />
        
        <Button
          variant="primary"
          onClick={startAssessment}
          disabled={!userId.trim()}
          className="w-full"
        >
          Iniciar Avaliação
        </Button>
      </div>
    </div>
  );

  // Renderiza uma pergunta de múltipla escolha
  const renderMultipleChoiceQuestion = () => {
    if (!currentQuestion || !currentQuestion.options) return null;
    
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-800">{currentQuestion.text}</h3>
        
        <RadioGroup
          name={`question-${currentQuestion.id}`}
          options={currentQuestion.options.map(opt => ({
            value: opt.value,
            label: opt.label,
            description: ''
          }))}
          value={userInput}
          onChange={setUserInput}
          className="mt-2"
        />
        
        <div className="flex justify-end mt-4">
          <Button
            variant="primary"
            onClick={() => handleAnswer(userInput)}
            disabled={!userInput}
          >
            Próxima
          </Button>
        </div>
      </div>
    );
  };

  // Renderiza uma pergunta aberta
  const renderOpenEndedQuestion = () => {
    if (!currentQuestion) return null;
    
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-800">{currentQuestion.text}</h3>
        
        <textarea
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 min-h-[120px]"
          placeholder="Digite sua resposta aqui..."
        />
        
        <div className="flex justify-end mt-4">
          <Button
            variant="primary"
            onClick={() => handleAnswer(userInput)}
            disabled={userInput.trim().length < 5}
          >
            Próxima
          </Button>
        </div>
      </div>
    );
  };

  // Renderiza a tela de conclusão
  const renderCompletionScreen = () => (
    <div className="text-center space-y-6">
      <div className="flex justify-center mb-4">
        <div className="p-3 bg-green-100 rounded-full">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      </div>
      
      <h3 className="text-xl font-semibold text-gray-800">Avaliação Concluída!</h3>
      
      <div className="bg-blue-50 p-4 rounded-lg text-left">
        <h4 className="font-medium text-blue-800 mb-2">Resumo da Avaliação:</h4>
        <ul className="space-y-2">
          <li className="flex items-center">
            <span className="font-medium mr-2">Nível identificado:</span>
            <span className="capitalize">{userLevel}</span>
          </li>
          <li className="flex items-center">
            <span className="font-medium mr-2">Formato preferido:</span>
            <span className="capitalize">{preferredFormat}</span>
          </li>
          <li>
            <span className="font-medium">Áreas para desenvolvimento:</span>
            {knowledgeGaps.length > 0 ? (
              <ul className="list-disc list-inside ml-2 mt-1">
                {knowledgeGaps.map((gap, index) => (
                  <li key={index}>{gap}</li>
                ))}
              </ul>
            ) : (
              <p className="ml-2 mt-1 text-sm">Nenhuma lacuna significativa identificada.</p>
            )}
          </li>
        </ul>
      </div>
      
      <p className="text-gray-600">
        Com base nesta avaliação, o sistema irá personalizar conteúdos e exercícios para seu perfil de aprendizado.
      </p>
      
      <Button
        variant="primary"
        onClick={() => {
          if (onComplete) {
            onComplete({
              userId,
              knowledgeGaps,
              preferredFormat,
              level: userLevel
            });
          }
        }}
      >
        Continuar para Conteúdos Personalizados
      </Button>
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <h2 className="text-xl font-bold">Avaliação de Conhecimento</h2>
        <p className="text-sm text-gray-600">
          Responda às perguntas para personalizar sua experiência de aprendizado
        </p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 bg-red-100 text-red-800 rounded-md">
            {error}
          </div>
        )}
        
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <p className="text-gray-600">Processando suas respostas...</p>
          </div>
        ) : (
          <div className="py-4">
            {currentStep === 0 && renderInitialScreen()}
            {currentStep > 0 && !assessmentComplete && currentQuestion?.type === 'multiple-choice' && renderMultipleChoiceQuestion()}
            {currentStep > 0 && !assessmentComplete && currentQuestion?.type === 'open-ended' && renderOpenEndedQuestion()}
            {assessmentComplete && renderCompletionScreen()}
          </div>
        )}
      </CardContent>
      
      {currentStep > 0 && !assessmentComplete && !isLoading && (
        <CardFooter className="flex justify-between">
          <div className="text-sm text-gray-500">
            Pergunta {questions.findIndex(q => q.id === currentQuestion?.id) + 1} de {questions.length}
          </div>
        </CardFooter>
      )}
    </Card>
  );
} 