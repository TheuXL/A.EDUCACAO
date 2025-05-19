from typing import List, Optional
import chromadb
from chromadb.api import Collection

from ...domain.entities.document import Document
from ...domain.interfaces.document_repository import DocumentRepository


class ChromaDocumentRepository(DocumentRepository):
    """
    Implementação do repositório de documentos usando ChromaDB.
    """
    
    def __init__(self, chroma_client: chromadb.Client, collection_name: str = "default_collection"):
        """
        Inicializa o repositório ChromaDB.
        
        Args:
            chroma_client: Cliente ChromaDB
            collection_name: Nome da coleção onde os documentos serão armazenados
        """
        self.client = chroma_client
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def add(self, document: Document) -> bool:
        """
        Adiciona um documento ao repositório ChromaDB.
        
        Args:
            document: Documento a ser adicionado
            
        Returns:
            True se adicionado com sucesso, False caso contrário
        """
        try:
            metadata = document.metadata or {}
            metadata["doc_type"] = document.doc_type.value
            
            self.collection.add(
                documents=[document.content],
                ids=[document.id],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            print(f"Erro ao adicionar documento ao ChromaDB: {e}")
            return False
            
    def add_batch(self, documents: List[Document]) -> bool:
        """
        Adiciona múltiplos documentos ao repositório ChromaDB.
        
        Args:
            documents: Lista de documentos a serem adicionados
            
        Returns:
            True se todos foram adicionados com sucesso, False caso contrário
        """
        if not documents:
            return False
            
        try:
            ids = []
            contents = []
            metadatas = []
            
            for doc in documents:
                ids.append(doc.id)
                contents.append(doc.content)
                
                metadata = doc.metadata or {}
                metadata["doc_type"] = doc.doc_type.value
                metadatas.append(metadata)
                
            self.collection.add(
                documents=contents,
                ids=ids,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Erro ao adicionar documentos em lote ao ChromaDB: {e}")
            return False
            
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Recupera um documento pelo ID.
        
        Args:
            document_id: ID do documento a ser recuperado
            
        Returns:
            Documento encontrado ou None se não existir
        """
        try:
            result = self.collection.get(ids=[document_id])
            
            if not result["documents"]:
                return None
                
            content = result["documents"][0]
            metadata = result["metadatas"][0] if result["metadatas"] else {}
            
            from ...domain.entities.document import DocumentType
            doc_type_value = metadata.pop("doc_type", "text")
            doc_type = DocumentType(doc_type_value)
            
            return Document(
                id=document_id,
                content=content,
                doc_type=doc_type,
                metadata=metadata
            )
        except Exception as e:
            print(f"Erro ao recuperar documento por ID: {e}")
            return None
            
    def search(self, query: str, limit: int = 5) -> List[Document]:
        """
        Busca documentos por similaridade.
        
        Args:
            query: Texto para busca por similaridade
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos ordenados por similaridade
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            documents = []
            if not results["documents"]:
                return documents
                
            from ...domain.entities.document import DocumentType
            
            for i, doc_id in enumerate(results["ids"][0]):
                content = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                doc_type_value = metadata.pop("doc_type", "text")
                doc_type = DocumentType(doc_type_value)
                
                documents.append(
                    Document(
                        id=doc_id,
                        content=content,
                        doc_type=doc_type,
                        metadata=metadata
                    )
                )
                
            return documents
        except Exception as e:
            print(f"Erro ao buscar documentos: {e}")
            return []
            
    def delete(self, document_id: str) -> bool:
        """
        Remove um documento do repositório.
        
        Args:
            document_id: ID do documento a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception as e:
            print(f"Erro ao deletar documento: {e}")
            return False 