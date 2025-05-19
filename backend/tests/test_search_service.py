import unittest
from unittest.mock import Mock, MagicMock
from typing import List

from ..app.domain.entities.document import Document, DocumentType
from ..app.domain.interfaces.document_repository import DocumentRepository
from ..app.domain.usecases.search_documents_usecase import SearchDocumentsUseCase
from ..services.search_service import SearchServiceImpl


class TestSearchService(unittest.TestCase):
    """
    Testes para o serviço de busca.
    """
    
    def setUp(self):
        """
        Configuração dos testes.
        """
        # Criar um mock do repositório de documentos
        self.mock_repository = Mock(spec=DocumentRepository)
        
        # Configurar o mock para retornar documentos de teste
        self.sample_documents = self._create_sample_documents()
        self.mock_repository.search.return_value = self.sample_documents
        self.mock_repository.get_by_id.return_value = self.sample_documents[0]
        
        # Inicializar o serviço de busca com o repositório mock
        self.search_service = SearchServiceImpl(document_repository=self.mock_repository)
        
        # Inicializar o caso de uso de busca
        self.search_usecase = SearchDocumentsUseCase(search_service=self.search_service)
        
    def _create_sample_documents(self) -> List[Document]:
        """
        Cria uma lista de documentos de exemplo para testes.
        
        Returns:
            Lista de documentos de exemplo
        """
        return [
            Document(
                id="doc1.txt",
                content="Este é um documento de texto para testes.",
                doc_type=DocumentType.TEXT,
                metadata={"source": "/path/to/doc1.txt", "size_bytes": 100}
            ),
            Document(
                id="doc2.pdf",
                content="Este é um documento PDF para testes.",
                doc_type=DocumentType.PDF,
                metadata={"source": "/path/to/doc2.pdf", "size_bytes": 200, "pages": 2}
            ),
            Document(
                id="doc3.json",
                content="Este é um documento JSON para testes.",
                doc_type=DocumentType.JSON,
                metadata={"source": "/path/to/doc3.json", "size_bytes": 150}
            )
        ]
        
    def test_search(self):
        """
        Testa a busca simples de documentos.
        """
        # Executar a busca
        query = "documento"
        limit = 3
        documents = self.search_service.search(query, limit)
        
        # Verificar se o método search do repositório foi chamado com os parâmetros corretos
        self.mock_repository.search.assert_called_once_with(query, limit)
        
        # Verificar se os documentos retornados são os esperados
        self.assertEqual(len(documents), len(self.sample_documents))
        self.assertEqual(documents[0].id, "doc1.txt")
        
    def test_search_with_filters(self):
        """
        Testa a busca com filtros.
        """
        # Configurar o mock para retornar todos os documentos
        self.mock_repository.search.return_value = self.sample_documents
        
        # Executar a busca com filtro por tipo de documento
        query = "documento"
        filters = {"doc_type": "pdf"}
        documents = self.search_service.search_with_filters(query, filters)
        
        # Verificar se o método search do repositório foi chamado
        self.mock_repository.search.assert_called_with(query, limit=10)  # limit * 2
        
        # Verificar se os documentos retornados são apenas os do tipo PDF
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].id, "doc2.pdf")
        self.assertEqual(documents[0].doc_type, DocumentType.PDF)
        
    def test_get_document(self):
        """
        Testa a recuperação de um documento pelo ID.
        """
        # Executar a recuperação do documento
        document_id = "doc1.txt"
        document = self.search_service.get_document(document_id)
        
        # Verificar se o método get_by_id do repositório foi chamado com o ID correto
        self.mock_repository.get_by_id.assert_called_once_with(document_id)
        
        # Verificar se o documento retornado é o esperado
        self.assertIsNotNone(document)
        self.assertEqual(document.id, document_id)
        
    def test_search_usecase(self):
        """
        Testa o caso de uso de busca.
        """
        # Executar a busca através do caso de uso
        query = "documento"
        documents = self.search_usecase.search(query)
        
        # Verificar se o método search do serviço de busca foi chamado
        self.mock_repository.search.assert_called_with(query, 5)  # 5 é o limite padrão
        
        # Verificar se os documentos retornados são os esperados
        self.assertEqual(len(documents), len(self.sample_documents))
        
    def test_search_usecase_empty_query(self):
        """
        Testa o caso de uso de busca com uma consulta vazia.
        """
        # Executar a busca com uma consulta vazia
        documents = self.search_usecase.search("")
        
        # Verificar se nenhum documento foi retornado (a consulta vazia não deve acionar a busca)
        self.assertEqual(len(documents), 0)
        
        # Verificar se o método search do serviço não foi chamado
        self.mock_repository.search.assert_not_called()
        
    def test_search_by_type(self):
        """
        Testa a busca por tipo de documento.
        """
        # Configurar o mock para retornar todos os documentos na busca search_with_filters
        self.search_service.search_with_filters = MagicMock(
            return_value=[doc for doc in self.sample_documents if doc.doc_type == DocumentType.TEXT]
        )
        
        # Executar a busca por tipo
        query = "documento"
        doc_type = "text"
        documents = self.search_usecase.search_by_type(query, doc_type)
        
        # Verificar se o método search_with_filters do serviço foi chamado com os parâmetros corretos
        self.search_service.search_with_filters.assert_called_once_with(
            query, {"doc_type": doc_type}, 5  # 5 é o limite padrão
        )
        
        # Verificar se os documentos retornados são apenas os do tipo TEXT
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].id, "doc1.txt")
        self.assertEqual(documents[0].doc_type, DocumentType.TEXT)


if __name__ == "__main__":
    unittest.main() 