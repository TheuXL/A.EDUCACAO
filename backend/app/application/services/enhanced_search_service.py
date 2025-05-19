from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import os

from backend.app.domain.entities.document import Document, DocumentType
from backend.app.domain.interfaces.document_repository import DocumentRepository
from backend.app.domain.interfaces.search_service import SearchService

class EnhancedSearchService(SearchService):
    """
    Implementação aprimorada do serviço de busca com recursos avançados:
    - Busca semântica mais precisa
    - Capacidade de filtrar por tipo de documento
    - Retorno de conteúdo baseado no formato preferido do usuário
    - Indicação de similaridade para resultados não exatos
    """
    
    def __init__(self, document_repository: DocumentRepository):
        """
        Inicializa o serviço de busca aprimorado.
        
        Args:
            document_repository: Repositório para acesso aos documentos
        """
        self.repository = document_repository
        self.similarity_threshold = 0.65  # Limiar para considerar uma correspondência como boa
        
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
            results = self.repository.search(query, limit=limit)
            return results
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
        Busca documentos com filtros específicos.
        
        Args:
            query: Texto da consulta
            filters: Dicionário de filtros a serem aplicados (e.g. {'doc_type': 'video'})
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos filtrados e ordenados por relevância
        """
        try:
            results = self.repository.search(query, limit=limit*3)
            
            filtered_results = []
            for doc in results:
                match = True
                
                for key, value in filters.items():
                    if key == 'doc_type' and hasattr(doc, 'doc_type'):
                        if doc.doc_type.value != value:
                            match = False
                            break
                    elif key.startswith('metadata.') and doc.metadata:
                        metadata_key = key.split('.')[1]
                        if metadata_key not in doc.metadata or doc.metadata[metadata_key] != value:
                            match = False
                            break
                
                if match:
                    filtered_results.append(doc)
                    
                if len(filtered_results) >= limit:
                    break
                    
            return filtered_results
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
            return self.repository.get_document_by_id(document_id)
        except Exception as e:
            print(f"Erro ao recuperar documento {document_id}: {e}")
            return None
    
    def search_by_format_preference(
        self, 
        query: str, 
        preferred_format: str = "texto", 
        limit: int = 5
    ) -> Tuple[List[Document], bool]:
        """
        Busca documentos priorizando o formato preferido do usuário.
        
        Args:
            query: Texto da consulta
            preferred_format: Formato preferido (texto, vídeo, imagem, áudio)
            limit: Número máximo de resultados
            
        Returns:
            Tupla com (lista de documentos, indicador de resposta exata)
        """
        format_to_doctype = {
            "texto": ["text", "pdf"],
            "vídeo": ["video"],
            "imagem": ["image"],
            "áudio": ["audio"]
        }
        
        preferred_doctypes = format_to_doctype.get(preferred_format.lower(), ["text", "pdf"])
        
        try:
            all_results = self.repository.search(query, limit=limit*2)
            
            preferred_results = []
            other_results = []
            
            for doc in all_results:
                if doc.doc_type.value in preferred_doctypes:
                    preferred_results.append(doc)
                else:
                    other_results.append(doc)
            
            if len(preferred_results) >= limit:
                results = preferred_results[:limit]
            else:
                results = preferred_results + other_results
                results = results[:limit]
            
            is_exact_match = False
            if results and len(results) > 0:
                top_result = results[0]
                
                if hasattr(top_result, 'embedding') and top_result.embedding:
                    similarity_score = getattr(top_result, '_similarity_score', 0.0)
                    is_exact_match = similarity_score > self.similarity_threshold
            
            return results, is_exact_match
            
        except Exception as e:
            print(f"Erro ao realizar busca por formato preferido: {e}")
            return [], False
    
    def search_by_type(self, query: str, doc_type: str, limit: int = 5) -> List[Document]:
        """
        Busca documentos de um tipo específico.
        
        Args:
            query: Consulta de busca
            doc_type: Tipo de documento (text, pdf, video, image, json)
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos do tipo especificado
        """
        return self.search_with_filters(
            query=query,
            filters={"doc_type": doc_type},
            limit=limit
        )
    
    def get_content_by_preferred_format(
        self, 
        document: Document, 
        format_type: str = "texto"
    ) -> Dict[str, Any]:
        """
        Extrai e formata o conteúdo do documento de acordo com o formato preferido.
        
        Args:
            document: Documento a ser processado
            format_type: Formato preferido do usuário (texto, vídeo, imagem, áudio)
            
        Returns:
            Dicionário com o conteúdo formatado e metadados
        """
        result = {
            "id": document.id,
            "type": document.doc_type.value,
            "content": document.content[:500] + "..." if len(document.content) > 500 else document.content,
            "metadata": document.metadata or {},
            "format_info": {}
        }
        
        if document.doc_type == DocumentType.VIDEO and format_type.lower() == "vídeo":
            result["format_info"] = {
                "is_video": True,
                "duration": document.metadata.get("duration_seconds", 0) if document.metadata else 0,
                "source_path": document.metadata.get("source", "") if document.metadata else "",
                "timestamps": document.metadata.get("timestamps", []) if document.metadata else []
            }
        
        elif document.doc_type == DocumentType.IMAGE and format_type.lower() == "imagem":
            result["format_info"] = {
                "is_image": True,
                "width": document.metadata.get("image_width", 0) if document.metadata else 0,
                "height": document.metadata.get("image_height", 0) if document.metadata else 0,
                "source_path": document.metadata.get("source", "") if document.metadata else ""
            }
            
        elif document.doc_type == DocumentType.PDF:
            result["format_info"] = {
                "is_pdf": True,
                "pages": document.metadata.get("pages", 0) if document.metadata else 0,
                "source_path": document.metadata.get("source", "") if document.metadata else ""
            }
            
        elif document.doc_type == DocumentType.AUDIO and format_type.lower() in ["áudio", "audio"]:
            result["format_info"] = {
                "is_audio": True,
                "duration": document.metadata.get("duration_seconds", 0) if document.metadata else 0,
                "source_path": document.metadata.get("source", "") if document.metadata else "",
                "timestamps": document.metadata.get("timestamps", []) if document.metadata else []
            }
        
        return result 