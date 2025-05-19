'use client';

import React from 'react';
import { PerformanceTest } from '@/components/admin/PerformanceTest';

export default function PerformancePage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Testes de Performance do Sistema</h1>
        <p className="text-gray-600">
          Utilize esta página para executar e analisar testes de performance do sistema A.Educação.
        </p>
      </div>
      
      <PerformanceTest />
      
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h2 className="text-lg font-medium mb-2">Sobre os Testes de Performance</h2>
        <p className="text-sm text-gray-600">
          Os testes avaliam diferentes aspectos do sistema:
        </p>
        <ul className="list-disc list-inside mt-2 text-sm text-gray-600 space-y-1">
          <li><strong>Indexação em Lote:</strong> Avalia o tempo necessário para indexar um grande número de arquivos de uma só vez.</li>
          <li><strong>Indexação em Tempo Real:</strong> Simula a criação de novos arquivos em intervalos definidos para avaliar a capacidade de processamento em tempo real.</li>
          <li><strong>Resposta da API:</strong> Mede o tempo de resposta médio da API durante consultas simultâneas.</li>
        </ul>
        <p className="mt-3 text-sm text-gray-600">
          Os resultados podem ser utilizados para identificar gargalos e otimizar o desempenho do sistema.
        </p>
      </div>
    </div>
  );
} 