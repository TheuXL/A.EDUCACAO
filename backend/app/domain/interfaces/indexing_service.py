from abc import ABC, abstractmethod
from pathlib import Path

class IndexingService(ABC):
    """
    Interface para serviços de indexação de documentos.
    Define o contrato para acesso a funcionalidades de indexação.
    """
    
    @abstractmethod
    def index_file(self, file_path: Path) -> bool:
        """
        Indexa um único arquivo.
        
        Args:
            file_path: Caminho do arquivo a ser indexado
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def index_directory(self, directory_path: Path) -> bool:
        """
        Indexa um diretório inteiro.
        
        Args:
            directory_path: Caminho do diretório a ser indexado
            
        Returns:
            True se pelo menos um arquivo foi indexado com sucesso
        """
        pass 