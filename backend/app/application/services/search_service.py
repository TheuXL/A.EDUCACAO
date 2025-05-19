from typing import List, Optional, Dict, Any

from backend.app.domain.entities.document import Document
from backend.app.domain.interfaces.document_repository import DocumentRepository
from backend.app.domain.interfaces.search_service import SearchService


class SearchServiceImpl(SearchService):
    """
    Implementação concreta do serviço de busca.
    Utiliza um repositório de documentos para realizar as buscas.
    """
    
    def __init__(self, document_repository: DocumentRepository):
        """
        Inicializa o serviço de busca com um repositório de documentos.
        
        Args:
            document_repository: Repositório para acesso aos documentos
        """
        self.repository = document_repository
        
    def search(self, query: str, limit: int = 5) -> List[Document]:
        """
        Busca documentos com base na consulta fornecida.
        
        Args:
            query: Texto da consulta
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos ordenados por relevância
        """
        try:
            return self.repository.search(query, limit)
        except Exception as e:
            print(f"Erro ao realizar busca: {e}")
            return []
            
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
            filters: Dicionário de filtros a serem aplicados
            limit: Número máximo de resultados a serem retornados
            
        Returns:
            Lista de documentos ordenados por relevância que correspondem aos filtros
        """
        try:
            # Realize a busca normal
            documents = self.repository.search(query, limit=limit * 2)  # Buscamos mais para poder filtrar depois
            
            # Filtra os resultados com base nos filtros fornecidos
            filtered_documents = []
            for document in documents:
                # Verifica se o documento atende a todos os filtros
                matches_all_filters = True
                
                for key, value in filters.items():
                    # Verifica o tipo do documento
                    if key == "doc_type" and hasattr(document, "doc_type"):
                        if document.doc_type.value != value:
                            matches_all_filters = False
                            break
                    # Verifica os metadados
                    elif document.metadata and key in document.metadata:
                        if document.metadata[key] != value:
                            matches_all_filters = False
                            break
                    else:
                        matches_all_filters = False
                        break
                
                if matches_all_filters:
                    filtered_documents.append(document)
                    
                if len(filtered_documents) >= limit:
                    break
                    
            return filtered_documents
        except Exception as e:
            print(f"Erro ao realizar busca com filtros: {e}")
            return []
            
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Recupera um documento específico pelo ID.
        
        Args:
            document_id: ID do documento a ser recuperado
            
        Returns:
            O documento se encontrado, None caso contrário
        """
        try:
            return self.repository.get_by_id(document_id)
        except Exception as e:
            print(f"Erro ao recuperar documento com ID {document_id}: {e}")
            return None 