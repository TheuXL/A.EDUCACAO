'use client';

import React, { useState } from 'react';
import { Tabs } from '@/components/ui/Tabs';
import { LearningGapsAnalysis } from '@/components/admin/LearningGapsAnalysis';
import { ImprovementPlan } from '@/components/admin/ImprovementPlan';

export default function LearningPage() {
  const [activeTab, setActiveTab] = useState('analysis');
  
  const tabs = [
    { id: 'analysis', label: 'Análise de Lacunas' },
    { id: 'plan', label: 'Plano de Melhoria' },
  ];
  
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Aprendizagem Adaptativa</h1>
        <p className="text-gray-600">
          Ferramentas para analisar lacunas de aprendizado e gerar planos de melhoria personalizados.
        </p>
      </div>
      
      <Tabs 
        tabs={tabs}
        activeTab={activeTab}
        onChange={setActiveTab}
        className="mb-6"
      />
      
      {activeTab === 'analysis' && (
        <LearningGapsAnalysis />
      )}
      
      {activeTab === 'plan' && (
        <ImprovementPlan />
      )}
    </div>
  );
} 