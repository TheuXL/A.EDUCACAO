from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..entities.document import Document


class SearchService(ABC):
    """
    Interface para o serviço de busca de documentos.
    Define a contrato para todas as implementações de serviços de busca.
    """
    
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Document]:
        """
        Busca documentos com base na consulta fornecida.
        
        Args:
            query: Texto da consulta
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos ordenados por relevância
        """
        pass
    
    @abstractmethod
    def search_with_filters(
        self, 
        query: str, 
        filters: Dict[str, Any], 
        limit: int = 5
    ) -> List[Document]:
        """
        Busca documentos com base na consulta e nos filtros fornecidos.
        
        Args:
            query: Texto da consulta
            filters: Dicionário de filtros a serem aplicados (e.g. {'doc_type': 'pdf'})
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos ordenados por relevância que correspondem aos filtros
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Recupera um documento específico pelo ID.
        
        Args:
            document_id: ID do documento a ser recuperado
            
        Returns:
            O documento se encontrado, None caso contrário
        """
        pass 