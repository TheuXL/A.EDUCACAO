import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { runPerformanceTest } from '@/services/api';

interface TestResults {
  batch_indexing?: {
    num_files: number;
    elapsed_time: number;
    indexing_rate: number;
  };
  realtime_indexing?: {
    num_files: number;
    total_time: number;
    avg_processing_time: number;
  };
  api_response?: {
    num_queries: number;
    avg_response_time: number;
    min_response_time: number;
    max_response_time: number;
  };
  system_info?: {
    cpu_count: number;
    total_memory: number;
    platform: string;
  };
}

export function PerformanceTest() {
  const [isLoading, setIsLoading] = useState(false);
  const [testDir, setTestDir] = useState('/tmp/aeducacao_test');
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [testType, setTestType] = useState('all');
  const [results, setResults] = useState<TestResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runTest = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await runPerformanceTest(testDir, apiUrl, testType);
      setResults(response);
    } catch (err: any) {
      setError(err.message || 'Erro ao executar teste de performance');
      console.error('Erro no teste de performance:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <h2 className="text-xl font-bold">Testes de Performance</h2>
        <p className="text-sm text-gray-600">Execute testes para avaliar o desempenho do sistema</p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Diretório de teste"
            value={testDir}
            onChange={(e) => setTestDir(e.target.value)}
            placeholder="/tmp/aeducacao_test"
          />
          
          <Input
            label="URL da API"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="http://localhost:8000"
          />
        </div>
        
        <Select
          label="Tipo de teste"
          value={testType}
          onChange={(e) => setTestType(e.target.value)}
          options={[
            { value: 'all', label: 'Todos os testes' },
            { value: 'batch', label: 'Indexação em lote' },
            { value: 'realtime', label: 'Indexação em tempo real' },
            { value: 'api', label: 'Tempo de resposta da API' }
          ]}
        />
        
        {error && (
          <div className="p-3 bg-red-100 text-red-800 rounded-md">
            {error}
          </div>
        )}
        
        {results && (
          <div className="space-y-4 mt-6">
            <h3 className="text-lg font-semibold">Resultados do Teste</h3>
            
            {results.batch_indexing && (
              <div className="p-4 bg-gray-50 rounded-md">
                <h4 className="font-medium mb-2">Indexação em Lote</h4>
                <ul className="space-y-1 text-sm">
                  <li>Número de arquivos: {results.batch_indexing.num_files}</li>
                  <li>Tempo total: {results.batch_indexing.elapsed_time.toFixed(2)} segundos</li>
                  <li>Taxa de indexação: {results.batch_indexing.indexing_rate.toFixed(2)} arquivos/segundo</li>
                </ul>
              </div>
            )}
            
            {results.realtime_indexing && (
              <div className="p-4 bg-gray-50 rounded-md">
                <h4 className="font-medium mb-2">Indexação em Tempo Real</h4>
                <ul className="space-y-1 text-sm">
                  <li>Número de arquivos: {results.realtime_indexing.num_files}</li>
                  <li>Tempo total: {results.realtime_indexing.total_time.toFixed(2)} segundos</li>
                  <li>Tempo médio de processamento: {results.realtime_indexing.avg_processing_time.toFixed(2)} segundos</li>
                </ul>
              </div>
            )}
            
            {results.api_response && (
              <div className="p-4 bg-gray-50 rounded-md">
                <h4 className="font-medium mb-2">Tempo de Resposta da API</h4>
                <ul className="space-y-1 text-sm">
                  <li>Número de consultas: {results.api_response.num_queries}</li>
                  <li>Tempo médio: {results.api_response.avg_response_time?.toFixed(2) || 'N/A'} segundos</li>
                  <li>Tempo mínimo: {results.api_response.min_response_time?.toFixed(2) || 'N/A'} segundos</li>
                  <li>Tempo máximo: {results.api_response.max_response_time?.toFixed(2) || 'N/A'} segundos</li>
                </ul>
              </div>
            )}
            
            {results.system_info && (
              <div className="p-4 bg-gray-50 rounded-md">
                <h4 className="font-medium mb-2">Informações do Sistema</h4>
                <ul className="space-y-1 text-sm">
                  <li>CPUs: {results.system_info.cpu_count}</li>
                  <li>Memória Total: {results.system_info.total_memory.toFixed(2)} GB</li>
                  <li>Plataforma: {results.system_info.platform}</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
      
      <CardFooter>
        <Button
          onClick={runTest}
          isLoading={isLoading}
          variant="primary"
        >
          Executar Teste
        </Button>
      </CardFooter>
    </Card>
  );
} 