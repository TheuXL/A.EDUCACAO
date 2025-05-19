import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ...domain.interfaces.indexing_service import IndexingService


class DirectoryWatcherService:
    """
    Serviço que monitora diretórios para indexação automática de novos arquivos.
    """
    
    def __init__(self, indexer_service: IndexingService, directories_to_watch: list[str]):
        """
        Inicializa o serviço de monitoramento.
        
        Args:
            indexer_service: Serviço de indexação para processar os arquivos
            directories_to_watch: Lista de diretórios a serem monitorados
        """
        self.indexer_service = indexer_service
        self.directories = directories_to_watch
        self.observer = Observer()
        self.running = False
        
    def start(self):
        """Inicia o monitoramento dos diretórios."""
        if self.running:
            return
            
        self.running = True
        
        # Configura o handler de eventos
        event_handler = FileChangeHandler(self.indexer_service)
        
        # Configura observers para cada diretório
        for directory in self.directories:
            path = Path(directory)
            if path.exists() and path.is_dir():
                self.observer.schedule(event_handler, str(path), recursive=True)
                print(f"Monitorando diretório: {path}")
                
        # Inicia o observer em uma thread separada
        self.observer.start()
        print(f"Monitoramento de diretórios iniciado para {len(self.directories)} diretórios")
        
    def stop(self):
        """Para o monitoramento dos diretórios."""
        if not self.running:
            return
            
        self.running = False
        self.observer.stop()
        self.observer.join()
        print("Monitoramento de diretórios encerrado")


class FileChangeHandler(FileSystemEventHandler):
    """
    Handler para eventos de sistema de arquivos.
    """
    
    def __init__(self, indexer_service: IndexingService):
        """
        Inicializa o handler de eventos.
        
        Args:
            indexer_service: Serviço de indexação para processar os arquivos
        """
        self.indexer_service = indexer_service
        self._cooldown = {}  # Evita processamento duplicado de eventos
        
    def on_created(self, event):
        """Processa novos arquivos."""
        if event.is_directory:
            return
            
        self._process_file(event.src_path)
        
    def on_modified(self, event):
        """Processa arquivos modificados."""
        if event.is_directory:
            return
            
        self._process_file(event.src_path)
        
    def _process_file(self, file_path: str):
        """
        Processa um arquivo para indexação com controle de cooldown
        para evitar múltiplas indexações do mesmo arquivo.
        
        Args:
            file_path: Caminho para o arquivo
        """
        current_time = time.time()
        
        # Verifica se o arquivo foi processado recentemente
        if file_path in self._cooldown:
            if current_time - self._cooldown[file_path] < 5:  # 5 segundos de cooldown
                return
                
        # Atualiza o timestamp do arquivo
        self._cooldown[file_path] = current_time
        
        # Inicia indexação em uma thread separada para não bloquear o watchdog
        threading.Thread(
            target=self._index_file, 
            args=(file_path,)
        ).start()
        
    def _index_file(self, file_path: str):
        """
        Indexa um único arquivo.
        
        Args:
            file_path: Caminho para o arquivo
        """
        try:
            path = Path(file_path)
            result = self.indexer_service.index_file(path)
            if result:
                print(f"Arquivo indexado automaticamente: {file_path}")
            else:
                print(f"Falha ao indexar automaticamente: {file_path}")
        except Exception as e:
            print(f"Erro ao indexar arquivo {file_path}: {e}") 