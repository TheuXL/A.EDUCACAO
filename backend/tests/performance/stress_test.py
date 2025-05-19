#!/usr/bin/env python3
"""
Script para teste de estresse e performance do sistema A.Educação.
Avalia especificamente o monitoramento de diretórios e indexação em tempo real.
"""
import os
import sys
import time
import random
import string
import argparse
import concurrent.futures
import shutil
import psutil
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import requests
import json
from tqdm import tqdm

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.application.services.indexer_service import IndexerService
from app.infrastructure.services.directory_watcher_service import DirectoryWatcherService
import chromadb


class PerformanceMonitor:
    """Monitora métricas de performance do sistema durante os testes."""
    
    def __init__(self, interval=1.0):
        self.interval = interval
        self.cpu_usage = []
        self.memory_usage = []
        self.timestamps = []
        self._stop = False
        
    def start(self):
        """Inicia o monitoramento em segundo plano."""
        self._stop = False
        self._start_time = time.time()
        
        # Inicia o monitoramento em uma thread separada
        import threading
        self.monitor_thread = threading.Thread(target=self._monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def _monitor(self):
        """Coleta métricas do sistema em intervalos regulares."""
        while not self._stop:
            # Coleta métricas
            self.cpu_usage.append(psutil.cpu_percent())
            self.memory_usage.append(psutil.virtual_memory().percent)
            self.timestamps.append(time.time() - self._start_time)
            
            # Aguarda o próximo intervalo
            time.sleep(self.interval)
    
    def stop(self):
        """Para o monitoramento."""
        self._stop = True
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)
    
    def plot(self, output_file=None):
        """Gera gráficos das métricas coletadas."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Gráfico de CPU
        ax1.plot(self.timestamps, self.cpu_usage, 'b-')
        ax1.set_title('CPU Usage')
        ax1.set_ylabel('Percent (%)')
        ax1.set_ylim(0, 100)
        ax1.grid(True)
        
        # Gráfico de Memória
        ax2.plot(self.timestamps, self.memory_usage, 'r-')
        ax2.set_title('Memory Usage')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Percent (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
            print(f"Gráficos salvos em {output_file}")
        else:
            plt.show()


def generate_random_file(directory, file_type, size_kb=10):
    """
    Gera um arquivo aleatório de um tipo específico.
    
    Args:
        directory: Diretório onde o arquivo será gerado
        file_type: Tipo de arquivo (txt, json, pdf)
        size_kb: Tamanho aproximado do arquivo em KB
    
    Returns:
        Caminho para o arquivo gerado
    """
    # Garante que o diretório existe
    os.makedirs(directory, exist_ok=True)
    
    # Gera um nome aleatório
    random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
    
    if file_type == 'txt':
        file_path = os.path.join(directory, f"{random_name}.txt")
        # Gera conteúdo aleatório
        content = ''.join(random.choices(string.ascii_letters + string.whitespace, k=size_kb * 1024))
        with open(file_path, 'w') as f:
            f.write(content)
    
    elif file_type == 'json':
        file_path = os.path.join(directory, f"{random_name}.json")
        # Cria um objeto JSON de exemplo
        data = {
            "title": "Exemplo de Conteúdo Educacional",
            "topic": "Aprendizagem Adaptativa",
            "content": ''.join(random.choices(string.ascii_letters + string.whitespace, k=size_kb * 512)),
            "metadata": {
                "author": "Teste de Performance",
                "date": time.strftime("%Y-%m-%d"),
                "tags": ["teste", "performance", "indexação"]
            }
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    elif file_type == 'pdf':
        # Para PDF, é mais simples copiar um arquivo de exemplo
        # Este teste supõe que existe um diretório 'samples' com arquivos de exemplo
        sample_dir = os.path.join(os.path.dirname(__file__), 'samples')
        
        if os.path.exists(sample_dir):
            sample_pdfs = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
            if sample_pdfs:
                source = os.path.join(sample_dir, random.choice(sample_pdfs))
                file_path = os.path.join(directory, f"{random_name}.pdf")
                shutil.copy(source, file_path)
            else:
                # Fallback para TXT se não houver PDFs de exemplo
                file_path = os.path.join(directory, f"{random_name}.txt")
                content = ''.join(random.choices(string.ascii_letters + string.whitespace, k=size_kb * 1024))
                with open(file_path, 'w') as f:
                    f.write(content)
        else:
            # Fallback para TXT se o diretório de amostras não existir
            file_path = os.path.join(directory, f"{random_name}.txt")
            content = ''.join(random.choices(string.ascii_letters + string.whitespace, k=size_kb * 1024))
            with open(file_path, 'w') as f:
                f.write(content)
    
    return file_path


def test_file_indexing_batch(indexer_service, test_dir, num_files=50, size_kb=10):
    """
    Testa a indexação de um lote de arquivos.
    
    Args:
        indexer_service: Serviço de indexação
        test_dir: Diretório para testes
        num_files: Número de arquivos a serem gerados
        size_kb: Tamanho aproximado de cada arquivo em KB
        
    Returns:
        Dict com resultados do teste
    """
    # Cria diretório de teste
    os.makedirs(test_dir, exist_ok=True)
    
    # Limpa arquivos anteriores
    for item in os.listdir(test_dir):
        item_path = os.path.join(test_dir, item)
        if os.path.isfile(item_path):
            os.unlink(item_path)
    
    print(f"Testando indexação em lote de {num_files} arquivos...")
    
    # Tipos de arquivo a serem gerados
    file_types = ['txt', 'json', 'pdf']
    file_paths = []
    
    # Gera arquivos
    for i in tqdm(range(num_files), desc="Gerando arquivos"):
        file_type = random.choice(file_types)
        file_path = generate_random_file(test_dir, file_type, size_kb)
        file_paths.append(file_path)
    
    # Mede o tempo para indexar
    start_time = time.time()
    
    # Indexa diretório
    success = indexer_service.index_directory(Path(test_dir))
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"Tempo de indexação em lote: {elapsed_time:.2f} segundos")
    print(f"Taxa de indexação: {num_files / elapsed_time:.2f} arquivos/segundo")
    
    return {
        "num_files": num_files,
        "elapsed_time": elapsed_time,
        "indexing_rate": num_files / elapsed_time,
        "success": success
    }


def test_realtime_indexing(indexer_service, test_dir, num_files=20, interval=0.5, size_kb=10):
    """
    Testa a indexação em tempo real com a criação/modificação de arquivos em intervalos.
    
    Args:
        indexer_service: Serviço de indexação
        test_dir: Diretório para testes
        num_files: Número de arquivos a serem gerados
        interval: Intervalo entre criação de arquivos (segundos)
        size_kb: Tamanho aproximado de cada arquivo em KB
        
    Returns:
        Dict com resultados do teste
    """
    # Configura o serviço de monitoramento
    watcher_service = DirectoryWatcherService(
        indexer_service=indexer_service,
        directories_to_watch=[test_dir]
    )
    
    # Inicia o monitoramento
    watcher_service.start()
    
    # Aguarda o monitoramento iniciar
    time.sleep(1)
    
    print(f"Testando indexação em tempo real de {num_files} arquivos...")
    
    # Tipos de arquivo a serem gerados
    file_types = ['txt', 'json', 'pdf']
    start_time = time.time()
    
    # Gera arquivos com intervalos
    for i in tqdm(range(num_files), desc="Criando arquivos"):
        file_type = random.choice(file_types)
        generate_random_file(test_dir, file_type, size_kb)
        time.sleep(interval)
    
    # Dá um tempo para a indexação terminar
    time.sleep(5)
    
    # Para o monitoramento
    watcher_service.stop()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Tempo total para indexação em tempo real: {total_time:.2f} segundos")
    
    return {
        "num_files": num_files,
        "total_time": total_time,
        "avg_processing_time": total_time / num_files,
        "interval": interval
    }


def test_api_response_time(base_url="http://localhost:8000", num_queries=10):
    """
    Testa o tempo de resposta da API.
    
    Args:
        base_url: URL base da API
        num_queries: Número de consultas a serem realizadas
        
    Returns:
        Dict com resultados do teste
    """
    print(f"Testando tempo de resposta da API com {num_queries} consultas...")
    
    # Consultas de exemplo
    sample_queries = [
        "O que é HTML?",
        "Como funciona a aprendizagem adaptativa?",
        "Explique o conceito de algoritmos de recomendação",
        "Quais são os benefícios da educação personalizada?",
        "Técnicas de análise de dados em educação",
        "Como criar tabelas em HTML?",
        "JavaScript para iniciantes",
        "Estruturas de repetição em programação",
        "Métodos de avaliação em educação online",
        "Inteligência artificial aplicada ao ensino"
    ]
    
    # Garante que temos consultas suficientes
    queries = []
    while len(queries) < num_queries:
        queries.extend(sample_queries)
    queries = queries[:num_queries]
    
    # Parâmetros de exemplo
    levels = ["iniciante", "intermediário", "avançado"]
    formats = ["texto", "vídeo", "imagem"]
    
    response_times = []
    
    # Realiza as consultas
    for i, query in enumerate(tqdm(queries, desc="Enviando consultas")):
        # Alterna entre níveis e formatos
        user_level = levels[i % len(levels)]
        preferred_format = formats[i % len(formats)]
        
        data = {
            "query": query,
            "user_level": user_level,
            "preferred_format": preferred_format
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/api/analyze", json=data)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = end_time - start_time
                response_times.append(response_time)
            else:
                print(f"Erro na consulta {i+1}: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"Erro na requisição: {e}")
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print(f"Tempo médio de resposta: {avg_response_time:.2f} segundos")
        print(f"Tempo mínimo: {min(response_times):.2f} segundos")
        print(f"Tempo máximo: {max(response_times):.2f} segundos")
        
        return {
            "num_queries": len(response_times),
            "avg_response_time": avg_response_time,
            "min_response_time": min(response_times),
            "max_response_time": max(response_times)
        }
    else:
        print("Não foi possível obter tempos de resposta.")
        return {
            "num_queries": 0,
            "avg_response_time": None,
            "min_response_time": None,
            "max_response_time": None
        }


def run_all_tests(test_dir, api_url=None):
    """
    Executa todos os testes e gera um relatório.
    
    Args:
        test_dir: Diretório para testes
        api_url: URL da API para testes (opcional)
    """
    os.makedirs(test_dir, exist_ok=True)
    
    # Cria diretório para resultados
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Configura o monitor de performance
    monitor = PerformanceMonitor(interval=0.5)
    
    try:
        # Inicializa serviço de indexação
        chroma_dir = os.path.join(results_dir, 'chromadb_test')
        os.makedirs(chroma_dir, exist_ok=True)
        
        chroma_client = chromadb.PersistentClient(path=chroma_dir)
        indexer_service = IndexerService(
            chroma_client=chroma_client,
            collection_name="test_collection"
        )
        
        # Inicia o monitor de performance
        monitor.start()
        
        # Teste 1: Indexação em lote
        batch_results = test_file_indexing_batch(
            indexer_service=indexer_service,
            test_dir=test_dir,
            num_files=50,
            size_kb=10
        )
        
        # Teste 2: Indexação em tempo real
        realtime_results = test_realtime_indexing(
            indexer_service=indexer_service,
            test_dir=test_dir,
            num_files=20,
            interval=0.5,
            size_kb=10
        )
        
        # Teste 3: Tempo de resposta da API (se URL fornecida)
        api_results = None
        if api_url:
            api_results = test_api_response_time(base_url=api_url, num_queries=10)
        
    finally:
        # Para o monitor de performance
        monitor.stop()
        
    # Gera gráficos
    monitor.plot(output_file=os.path.join(results_dir, 'performance_metrics.png'))
    
    # Gera relatório
    report = {
        "batch_indexing": batch_results,
        "realtime_indexing": realtime_results,
        "api_response": api_results,
        "system_info": {
            "cpu_count": psutil.cpu_count(),
            "total_memory": psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
            "platform": sys.platform
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Salva relatório em JSON
    with open(os.path.join(results_dir, 'performance_report.json'), 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n=== Relatório de Performance ===")
    print(f"Relatório salvo em {os.path.join(results_dir, 'performance_report.json')}")
    print(f"Gráficos salvos em {os.path.join(results_dir, 'performance_metrics.png')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste de estresse e performance do A.Educação")
    parser.add_argument("--test-dir", type=str, default="/tmp/aeducacao_test",
                      help="Diretório para arquivos de teste")
    parser.add_argument("--api-url", type=str, default=None,
                      help="URL da API para testes (ex: http://localhost:8000)")
    args = parser.parse_args()
    
    run_all_tests(args.test_dir, args.api_url) 