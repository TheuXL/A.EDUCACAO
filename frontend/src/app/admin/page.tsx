'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';

export default function AdminPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Painel Administrativo</h1>
        <p className="text-gray-600">
          Bem-vindo ao painel administrativo do sistema A.Educação.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link href="/admin/performance" className="block transition-transform hover:scale-105">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-full text-blue-600">
                  PERF
                </div>
                <h3 className="text-lg font-medium">Testes de Performance</h3>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Execute e analise testes de performance do sistema, incluindo indexação em lote, em tempo real e tempo de resposta da API.
              </p>
            </CardContent>
          </Card>
        </Link>
        
        {/* Outros cards de funcionalidades administrativas podem ser adicionados aqui */}
      </div>
    </div>
  );
} 