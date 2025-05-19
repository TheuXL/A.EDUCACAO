'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { InteractivePrompt } from '@/components/content/InteractivePrompt';
import { AdaptiveLearningContent } from '@/components/content/AdaptiveLearningContent';

interface AssessmentResult {
  userId: string;
  knowledgeGaps: string[];
  preferredFormat: string;
  level: string;
}

export default function LearningPage() {
  const [assessmentComplete, setAssessmentComplete] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult | null>(null);

  const handleAssessmentComplete = (result: AssessmentResult) => {
    setAssessmentResult(result);
    setAssessmentComplete(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto py-4 px-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
              A
            </div>
            <Link href="/" className="text-xl font-bold text-gray-900">A.Educação</Link>
          </div>
          <nav>
            <ul className="flex space-x-6">
              <li>
                <Link href="/" className="text-gray-700 hover:text-blue-600 transition">
                  Início
                </Link>
              </li>
              <li>
                <Link href="/learning" className="text-blue-600 font-medium">
                  Aprendizado Adaptativo
                </Link>
              </li>
              <li>
                <Link href="/admin" className="text-gray-700 hover:text-blue-600 transition">
                  Admin
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Aprendizado Adaptativo</h1>
            <p className="text-lg text-gray-600">
              Identifique suas lacunas de conhecimento e receba conteúdo personalizado para melhorar seu aprendizado.
            </p>
          </div>

          {!assessmentComplete ? (
            <InteractivePrompt onComplete={handleAssessmentComplete} />
          ) : (
            <>
              {assessmentResult && (
                <div className="space-y-8">
                  <AdaptiveLearningContent
                    userId={assessmentResult.userId}
                    knowledgeGaps={assessmentResult.knowledgeGaps}
                    preferredFormat={assessmentResult.preferredFormat}
                    level={assessmentResult.level}
                  />
                  
                  <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4">Seu Plano de Aprendizado</h2>
                    <p className="text-gray-600 mb-4">
                      Com base na sua avaliação, criamos um plano de aprendizado personalizado para você.
                      Continue explorando os tópicos abaixo para melhorar suas habilidades.
                    </p>
                    
                    {assessmentResult.knowledgeGaps.length > 0 ? (
                      <div className="space-y-4">
                        <h3 className="text-lg font-medium">Áreas para desenvolvimento:</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {assessmentResult.knowledgeGaps.map((gap, index) => (
                            <div 
                              key={index}
                              className="p-4 bg-blue-50 rounded-lg border border-blue-100 flex items-center"
                            >
                              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold mr-3">
                                {index + 1}
                              </div>
                              <div>
                                <h4 className="font-medium">{gap}</h4>
                                <p className="text-sm text-gray-600">Clique no tópico atual para ver o conteúdo</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-center p-4 bg-gray-50 rounded-lg">
                        Nenhuma lacuna significativa identificada. Continue praticando!
                      </p>
                    )}
                    
                    <div className="mt-6 pt-4 border-t border-gray-200">
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="font-medium">Formato preferido: <span className="capitalize text-blue-600">{assessmentResult.preferredFormat}</span></h4>
                          <p className="text-sm text-gray-600">O conteúdo será priorizado neste formato quando disponível</p>
                        </div>
                        <Link href="/">
                          <button className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors">
                            Voltar ao Início
                          </button>
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-6 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; {new Date().getFullYear()} A.Educação. Todos os direitos reservados.</p>
        </div>
      </footer>
    </div>
  );
} 