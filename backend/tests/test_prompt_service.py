import unittest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from ..app.domain.entities.document import Document, DocumentType
from ..app.domain.interfaces.search_service import SearchService
from ..app.domain.interfaces.user_progress_repository import UserProgressRepository
from ..app.domain.usecases.generate_adaptive_response_usecase import GenerateAdaptiveResponseUseCase
from ..services.prompt_service import PromptServiceImpl


class TestPromptService(unittest.TestCase):
    """
    Testes para o serviço de prompt.
    """
    
    def setUp(self):
        """
        Configuração dos testes.
        """
        # Criar mocks para as dependências
        self.mock_search_service = Mock(spec=SearchService)
        self.mock_user_progress_repository = Mock(spec=UserProgressRepository)
        
        # Configurar o mock do serviço de busca para retornar documentos de teste
        self.sample_documents = self._create_sample_documents()
        self.mock_search_service.search.return_value = self.sample_documents
        
        # Inicializar o serviço de prompt com os mocks
        self.prompt_service = PromptServiceImpl(
            search_service=self.mock_search_service,
            user_progress_repository=self.mock_user_progress_repository
        )
        
        # Inicializar o caso de uso
        self.response_usecase = GenerateAdaptiveResponseUseCase(
            prompt_service=self.prompt_service
        )
        
    def _create_sample_documents(self) -> List[Document]:
        """
        Cria uma lista de documentos de exemplo para testes.
        
        Returns:
            Lista de documentos de exemplo
        """
        return [
            Document(
                id="doc1.txt",
                content="Este é um documento de texto para testes. Ele contém informações sobre aprendizagem adaptativa. "
                        "O conteúdo adaptativo ajuda estudantes a aprender no seu próprio ritmo.",
                doc_type=DocumentType.TEXT,
                metadata={
                    "source": "/path/to/doc1.txt", 
                    "size_bytes": 100,
                    "title": "Introdução à Aprendizagem Adaptativa"
                }
            ),
            Document(
                id="doc2.pdf",
                content="Este é um documento PDF para testes sobre educação. A educação moderna utiliza "
                        "tecnologia para personalizar o aprendizado. Inteligência artificial "
                        "pode ajudar a identificar pontos fortes e fracos dos estudantes.",
                doc_type=DocumentType.PDF,
                metadata={
                    "source": "/path/to/doc2.pdf", 
                    "size_bytes": 200, 
                    "pages": 2,
                    "title": "Educação e Tecnologia"
                }
            ),
            Document(
                id="doc3.mp4",
                content="Transcrição de vídeo sobre métodos de ensino. Métodos modernos focam em "
                        "experiência prática e personalização. O feedback imediato é essencial para o aprendizado.",
                doc_type=DocumentType.VIDEO,
                metadata={
                    "source": "/path/to/doc3.mp4", 
                    "duration": "10:30",
                    "title": "Métodos Modernos de Ensino"
                }
            )
        ]
        
    def test_generate_response(self):
        """
        Testa a geração de resposta adaptativa.
        """
        # Executar a geração de resposta
        query = "aprendizagem adaptativa"
        user_level = "intermediário"
        preferred_format = "texto"
        
        response = self.prompt_service.generate_response(
            query=query,
            user_level=user_level,
            preferred_format=preferred_format
        )
        
        # Verificar se o método search do serviço de busca foi chamado
        self.mock_search_service.search.assert_called_once()
        
        # Verificar se a resposta não está vazia
        self.assertTrue(response)
        
        # Verificar se a resposta contém informações relevantes
        self.assertIn("aprendizagem adaptativa", response.lower())
        
    def test_generate_response_empty_results(self):
        """
        Testa a geração de resposta quando não há resultados.
        """
        # Configurar o mock para retornar uma lista vazia
        self.mock_search_service.search.return_value = []
        
        # Executar a geração de resposta
        query = "tema inexistente"
        response = self.prompt_service.generate_response(query=query)
        
        # Verificar se a resposta contém uma mensagem de erro apropriada
        self.assertIn("não encontrei informações sobre", response.lower())
        
    def test_suggest_related_content(self):
        """
        Testa a sugestão de conteúdos relacionados.
        """
        # Executar a sugestão de conteúdos
        query = "educação"
        suggestions = self.prompt_service.suggest_related_content(query=query, limit=2)
        
        # Verificar se o método search do serviço de busca foi chamado
        self.mock_search_service.search.assert_called_once()
        
        # Verificar se as sugestões foram retornadas
        self.assertEqual(len(suggestions), 2)
        
        # Verificar se as sugestões contêm as informações esperadas
        self.assertIn("id", suggestions[0])
        self.assertIn("type", suggestions[0])
        self.assertIn("title", suggestions[0])
        self.assertIn("preview", suggestions[0])
        
    def test_store_user_interaction(self):
        """
        Testa o armazenamento de interações do usuário.
        """
        # Configurar o mock para retornar True
        self.mock_user_progress_repository.update_interaction.return_value = True
        
        # Executar o armazenamento de interação
        user_id = "user123"
        query = "aprendizagem adaptativa"
        response = "Resposta de teste"
        result = self.prompt_service.store_user_interaction(
            user_id=user_id,
            query=query,
            response=response
        )
        
        # Verificar se o método update_interaction do repositório foi chamado
        self.mock_user_progress_repository.update_interaction.assert_called_once_with(
            user_id=user_id,
            query=query,
            response=response,
            feedback=None
        )
        
        # Verificar se o resultado é True
        self.assertTrue(result)
        
    def test_extract_keywords(self):
        """
        Testa a extração de palavras-chave de uma consulta.
        """
        query = "Como funciona a aprendizagem adaptativa na educação moderna?"
        keywords = self.prompt_service._extract_keywords(query)
        
        # Verificar se as palavras-chave foram extraídas corretamente
        expected_keywords = ["como", "funciona", "aprendizagem", "adaptativa", "educação", "moderna"]
        for keyword in expected_keywords:
            self.assertIn(keyword, keywords)
            
        # Verificar se as stop words foram removidas
        stop_words = ["a", "na"]
        for word in stop_words:
            self.assertNotIn(word, keywords)
            
    def test_format_response_for_different_levels(self):
        """
        Testa a formatação da resposta para diferentes níveis de usuário.
        """
        query = "aprendizagem adaptativa"
        excerpts = [(self.sample_documents[0], "Trecho de teste sobre aprendizagem adaptativa.")]
        
        # Teste para nível iniciante
        response_iniciante = self.prompt_service._format_response(
            query=query,
            excerpts=excerpts,
            user_level="iniciante",
            preferred_format="texto"
        )
        self.assertIn("explicação simples", response_iniciante.lower())
        
        # Teste para nível intermediário
        response_intermediario = self.prompt_service._format_response(
            query=query,
            excerpts=excerpts,
            user_level="intermediário",
            preferred_format="texto"
        )
        self.assertIn("encontrei estas informações", response_intermediario.lower())
        
        # Teste para nível avançado
        response_avancado = self.prompt_service._format_response(
            query=query,
            excerpts=excerpts,
            user_level="avançado",
            preferred_format="texto"
        )
        self.assertIn("análise detalhada", response_avancado.lower())
        
    def test_generate_adaptive_response_usecase(self):
        """
        Testa o caso de uso para geração de resposta adaptativa.
        """
        # Executar a geração de resposta através do caso de uso
        query = "aprendizagem adaptativa"
        user_level = "intermediário"
        preferred_format = "texto"
        
        response = self.response_usecase.generate_response(
            query=query,
            user_level=user_level,
            preferred_format=preferred_format
        )
        
        # Verificar se a resposta não está vazia
        self.assertTrue(response)
        
        # Verificar se o método generate_response do serviço de prompt foi chamado
        self.mock_search_service.search.assert_called_once()
        
    def test_extract_relevant_excerpt(self):
        """
        Testa a extração de trechos relevantes.
        """
        content = "Este é um parágrafo sobre educação. Educação adaptativa é importante. " \
                 "Personalização ajuda estudantes. Tecnologia facilita a educação adaptativa."
        keywords = ["educação", "adaptativa", "personalização"]
        max_length = 100
        
        excerpt = self.prompt_service._extract_relevant_excerpt(content, keywords, max_length)
        
        # Verificar se o trecho extraído contém as palavras-chave
        self.assertIn("educação", excerpt.lower())
        self.assertIn("adaptativa", excerpt.lower())
        
        # Verificar se o tamanho do trecho está dentro do limite
        self.assertLessEqual(len(excerpt), max_length)


if __name__ == "__main__":
    unittest.main() 