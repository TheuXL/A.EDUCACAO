from typing import List, Optional, Dict, Any

from ..entities.document import Document
from ..interfaces.search_service import SearchService


class SearchDocumentsUseCase:
    """
    Caso de uso para busca de documentos.
    Encapsula a lógica de busca e pode adicionar regras de negócio adicionais.
    """
    
    def __init__(self, search_service: SearchService):
        """
        Inicializa o caso de uso com um serviço de busca.
        
        Args:
            search_service: Implementação concreta de um serviço de busca
        """
        self.search_service = search_service
        
    def search(self, query: str, limit: int = 5) -> List[Document]:
        """
        Realiza uma busca simples por documentos.
        
        Args:
            query: Texto da consulta
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos ordenados por relevância
        """
        # Aqui poderiam ser adicionadas regras de negócio adicionais,
        # como validação da consulta, transformação da consulta, etc.
        
        if not query.strip():
            return []
            
        return self.search_service.search(query, limit)
        
    def search_by_type(
        self, 
        query: str, 
        doc_type: str, 
        limit: int = 5
    ) -> List[Document]:
        """
        Busca documentos de um tipo específico.
        
        Args:
            query: Texto da consulta
            doc_type: Tipo de documento (pdf, text, etc.)
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos do tipo especificado ordenados por relevância
        """
        filters = {"doc_type": doc_type}
        return self.search_service.search_with_filters(query, filters, limit)
        
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Recupera um documento específico pelo ID.
        
        Args:
            document_id: ID do documento a ser recuperado
            
        Returns:
            O documento se encontrado, None caso contrário
        """
        return self.search_service.get_document(document_id)
        
    def search_with_advanced_filters(
        self, 
        query: str, 
        filters: Dict[str, Any], 
        limit: int = 5
    ) -> List[Document]:
        """
        Realiza uma busca com filtros avançados.
        
        Args:
            query: Texto da consulta
            filters: Dicionário de filtros a serem aplicados
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos que correspondem aos filtros ordenados por relevância
        """
        # Aqui poderiam ser adicionadas regras de negócio adicionais,
        # como validação e transformação dos filtros
        
        return self.search_service.search_with_filters(query, filters, limit) 