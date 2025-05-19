from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.document import Document


class DocumentRepository(ABC):
    """
    Interface para repositório de documentos.
    Segue o princípio de inversão de dependência.
    """
    
    @abstractmethod
    def add(self, document: Document) -> bool:
        """Adiciona um documento ao repositório."""
        pass
    
    @abstractmethod
    def add_batch(self, documents: List[Document]) -> bool:
        """Adiciona múltiplos documentos ao repositório."""
        pass
    
    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Recupera um documento pelo ID."""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Document]:
        """Busca documentos por similaridade."""
        pass
    
    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """Remove um documento do repositório."""
        pass 