from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

from ..entities.document import Document


class DocumentParser(ABC):
    """
    Interface para parsers de documentos.
    Define como diferentes tipos de documentos são processados para indexação.
    """
    
    @abstractmethod
    def parse(self, file_path: Path) -> Optional[Document]:
        """
        Processa um arquivo e retorna um objeto Document.
        
        Args:
            file_path: Caminho para o arquivo a ser processado
        
        Returns:
            Document com o conteúdo processado ou None se o processamento falhar
        """
        pass
    
    @abstractmethod
    def supports_extension(self, extension: str) -> bool:
        """
        Verifica se este parser suporta a extensão do arquivo.
        
        Args:
            extension: Extensão do arquivo (sem o ponto)
        
        Returns:
            True se o parser suporta esta extensão, False caso contrário
        """
        pass 