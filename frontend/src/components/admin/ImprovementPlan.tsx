import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import api from '@/services/api';

interface ImprovementPlanResult {
  user_id: string;
  status: string;
  creation_date?: string;
  recommended_completion_date?: string;
  plan_title?: string;
  steps: Array<{
    id: string;
    title: string;
    description: string;
    resource_type: string;
    estimated_time: string;
    difficulty: string;
  }>;
  overall_goal?: string;
  message?: string;
}

export function ImprovementPlan() {
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState('');
  const [plan, setPlan] = useState<ImprovementPlanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generatePlan = async () => {
    if (!userId.trim()) {
      setError('ID do usuário é obrigatório');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get<ImprovementPlanResult>(`/api/learning/improvement-plan/${userId}`);
      setPlan(response.data);
    } catch (err: any) {
      setError(err.message || 'Erro ao gerar plano de melhoria');
      console.error('Erro ao gerar plano:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Função para formatar uma data legível
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('pt-BR', { 
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric'
    });
  };

  // Função para retornar a cor do badge de dificuldade
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'fácil': return 'bg-green-100 text-green-800';
      case 'médio': return 'bg-yellow-100 text-yellow-800';
      case 'difícil': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Função para exibir ícone com base no tipo de recurso
  const getResourceTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'artigo':
      case 'texto':
        return '📄';
      case 'vídeo':
        return '📹';
      case 'exercício':
        return '✏️';
      case 'quiz':
        return '❓';
      case 'simulação':
        return '🔄';
      default:
        return '📚';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <h2 className="text-xl font-bold">Plano de Melhoria</h2>
        <p className="text-sm text-gray-600">Gere um plano de aprendizado personalizado com base nas lacunas identificadas</p>
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
          
          <div className="flex items-end">
            <Button
              onClick={generatePlan}
              isLoading={isLoading}
              variant="primary"
              disabled={!userId.trim()}
            >
              Gerar Plano
            </Button>
          </div>
        </div>
        
        {error && (
          <div className="p-3 bg-red-100 text-red-800 rounded-md">
            {error}
          </div>
        )}
        
        {plan && plan.status === 'success' && (
          <div className="space-y-6 mt-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-xl font-semibold text-blue-800">{plan.plan_title || 'Plano de Melhoria Personalizado'}</h3>
              
              <div className="mt-3 text-sm">
                <div className="flex justify-between mb-2">
                  <span className="text-gray-600">Criado em:</span>
                  <span className="font-medium">{formatDate(plan.creation_date)}</span>
                </div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-600">Conclusão recomendada:</span>
                  <span className="font-medium">{formatDate(plan.recommended_completion_date)}</span>
                </div>
              </div>
              
              {plan.overall_goal && (
                <div className="mt-4 p-3 bg-white rounded-md border border-blue-200">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Objetivo Geral</h4>
                  <p className="text-sm">{plan.overall_goal}</p>
                </div>
              )}
            </div>
            
            <div>
              <h4 className="font-medium text-lg mb-4">Passos do Plano</h4>
              
              {plan.steps.length > 0 ? (
                <ol className="space-y-4">
                  {plan.steps.map((step, index) => (
                    <li key={step.id} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full text-blue-800 font-bold">
                          {index + 1}
                        </div>
                        <h5 className="font-medium text-gray-900">{step.title}</h5>
                      </div>
                      
                      <p className="text-sm text-gray-700 mb-3 pl-11">{step.description}</p>
                      
                      <div className="flex flex-wrap items-center gap-3 pl-11 text-sm">
                        <div className="flex items-center">
                          <span className="mr-2">{getResourceTypeIcon(step.resource_type)}</span>
                          <span>{step.resource_type}</span>
                        </div>
                        
                        <div className="flex items-center">
                          <span className="mr-2">⏱️</span>
                          <span>{step.estimated_time}</span>
                        </div>
                        
                        <span className={`px-2 py-0.5 rounded-full ${getDifficultyColor(step.difficulty)}`}>
                          {step.difficulty}
                        </span>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-center p-6 bg-gray-50 rounded-lg text-gray-500">
                  Nenhum passo definido no plano
                </p>
              )}
            </div>
          </div>
        )}
        
        {plan && plan.status !== 'success' && (
          <div className="p-4 bg-yellow-50 text-yellow-800 rounded-md">
            {plan.message || 'Não foi possível gerar um plano para este usuário. Verifique se o usuário existe e possui histórico suficiente.'}
          </div>
        )}
      </CardContent>
    </Card>
  );
} 