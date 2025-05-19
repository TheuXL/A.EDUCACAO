from pathlib import Path
import chromadb
from typing import Optional, List, Tuple

from backend.app.domain.interfaces.document_repository import DocumentRepository
from backend.app.domain.usecases.index_document_usecase import IndexDocumentUseCase
from backend.app.infrastructure.repositories.chroma_document_repository import ChromaDocumentRepository
from backend.app.infrastructure.parsers.parser_registry import ParserRegistry
from backend.app.domain.usecases.search_documents_usecase import SearchDocumentsUseCase
from backend.app.domain.interfaces.transcription_service import TranscriptionService
from backend.app.domain.interfaces.ocr_service import OCRService
from backend.app.domain.interfaces.indexing_service import IndexingService
from backend.app.infrastructure.services.whisper_transcription_service import WhisperTranscriptionService
from backend.app.infrastructure.services.tesseract_ocr_service import TesseractOCRService
from backend.app.application.services.search_service import SearchServiceImpl
from backend.app.domain.entities.document import Document
from backend.app.domain.interfaces.user_progress_repository import UserProgressRepository
from backend.app.infrastructure.repositories.json_user_progress_repository import JsonUserProgressRepository

# Importa opcionalmente o serviço de rede neural
try:
    from backend.app.application.services.neural_network_service import NeuralNetworkService
except ImportError:
    print("AVISO: PyTorch não está instalado. Recursos de rede neural não estarão disponíveis.")
    NeuralNetworkService = None


class IndexerService(IndexingService):
    """
    Serviço de indexação que utiliza a arquitetura limpa.
    Este serviço é uma fachada (facade) sobre os casos de uso e infraestrutura subjacentes.
    """
    
    def __init__(
        self, 
        chroma_client: chromadb.Client = None, 
        collection_name: str = "default_collection",
        transcription_service: Optional[TranscriptionService] = None,
        ocr_service: Optional[OCRService] = None,
        user_progress_repository: Optional[UserProgressRepository] = None
    ):
        """
        Inicializa o serviço de indexação.
        
        Args:
            chroma_client: Cliente ChromaDB. Se não for fornecido, cria um cliente em memória.
            collection_name: Nome da coleção onde os documentos serão armazenados.
            transcription_service: Serviço de transcrição para vídeos. Se não for fornecido,
                                  tenta criar um WhisperTranscriptionService.
            ocr_service: Serviço de OCR para imagens. Se não for fornecido,
                         tenta criar um TesseractOCRService.
            user_progress_repository: Repositório para armazenamento do progresso do usuário.
        """
        if not chroma_client:
            chroma_client = chromadb.Client()
            
        self.repository: DocumentRepository = ChromaDocumentRepository(
            chroma_client=chroma_client,
            collection_name=collection_name
        )
        
        self.transcription_service = transcription_service
        if not self.transcription_service:
            try:
                self.transcription_service = WhisperTranscriptionService(model_size="base")
            except ImportError:
                print("AVISO: Whisper não está instalado. A indexação de vídeos não será suportada.")
                self.transcription_service = None
                
        self.ocr_service = ocr_service
        if not self.ocr_service:
            try:
                self.ocr_service = TesseractOCRService()
            except ImportError:
                print("AVISO: Tesseract não está instalado. A indexação de imagens não será suportada.")
                self.ocr_service = None
        
        self.user_progress_repository = user_progress_repository
        if not self.user_progress_repository:
            self.user_progress_repository = JsonUserProgressRepository()
        
        self.parser_registry = ParserRegistry(
            transcription_service=self.transcription_service,
            ocr_service=self.ocr_service
        )
        
        self.index_usecase = IndexDocumentUseCase(
            document_repository=self.repository,
            parsers=self.parser_registry.get_all_parsers()
        )
        
        self.search_service = SearchServiceImpl(document_repository=self.repository)
        self.search_usecase = SearchDocumentsUseCase(search_service=self.search_service)
        
        self.neural_network_service = None
        if NeuralNetworkService:
            try:
                self.neural_network_service = NeuralNetworkService(
                    user_progress_repository=self.user_progress_repository
                )
                print("Serviço de rede neural inicializado com sucesso.")
            except Exception as e:
                print(f"Erro ao inicializar serviço de rede neural: {e}")
        
    def index_text(self, text_path: str) -> bool:
        """
        Indexa um arquivo de texto.
        
        Args:
            text_path: Caminho para o arquivo de texto
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        file_path = Path(text_path)
        return self.index_file(file_path)
        
    def index_pdf(self, pdf_path: str) -> bool:
        """
        Indexa um arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        file_path = Path(pdf_path)
        return self.index_file(file_path)
        
    def index_video(self, video_path: str) -> bool:
        """
        Indexa um arquivo de vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        if not self.transcription_service:
            print("Erro: Serviço de transcrição não disponível.")
            return False
            
        file_path = Path(video_path)
        return self.index_file(file_path)
        
    def index_image(self, image_path: str) -> bool:
        """
        Indexa um arquivo de imagem.
        
        Args:
            image_path: Caminho para o arquivo de imagem
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        if not self.ocr_service:
            print("Erro: Serviço de OCR não disponível.")
            return False
            
        file_path = Path(image_path)
        return self.index_file(file_path)
        
    def index_audio(self, audio_path: str) -> bool:
        """
        Indexa um arquivo de áudio.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        if not self.transcription_service:
            print("Erro: Serviço de transcrição não disponível.")
            return False
            
        file_path = Path(audio_path)
        return self.index_file(file_path)
        
    def index_data(self, data_dir: str) -> bool:
        """
        Indexa todos os arquivos suportados no diretório.
        
        Args:
            data_dir: Caminho do diretório com arquivos a serem indexados
            
        Returns:
            True se pelo menos um arquivo foi indexado com sucesso, False caso contrário
        """
        directory = Path(data_dir)
        success = self.index_directory(directory)
        
        if success:
            self.verify_indexing()
            
        return success
        
    def index_file(self, file_path: Path) -> bool:
        """
        Implementação da interface IndexingService.
        Indexa um único arquivo.
        
        Args:
            file_path: Caminho do arquivo a ser indexado
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        success = self.index_usecase.index_file(file_path)
        
        if success and self.neural_network_service:
            try:
                self.neural_network_service.update_from_user_interactions()
            except Exception as e:
                print(f"Aviso: Falha ao atualizar modelos de aprendizado: {e}")
        
        return success

    def index_directory(self, directory_path: Path) -> bool:
        """
        Implementação da interface IndexingService.
        Indexa todos os arquivos suportados em um diretório.
        
        Args:
            directory_path: Caminho do diretório com arquivos a serem indexados
            
        Returns:
            True se pelo menos um arquivo foi indexado com sucesso, False caso contrário
        """
        return self.index_usecase.index_directory(directory_path)
        
    def verify_indexing(self) -> bool:
        """
        Verifica se a indexação foi bem-sucedida realizando uma busca simples.
        
        Returns:
            True se conseguir recuperar documentos, False caso contrário
        """
        try:
            docs = self.search_service.search("test", limit=1)
            return len(docs) > 0
        except Exception as e:
            print(f"Erro ao verificar indexação: {e}")
            return False
        
    def search(self, query: str, limit: int = 5):
        """
        Realiza uma busca nos documentos indexados.
        
        Args:
            query: Consulta de busca
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes
        """
        return self.search_service.search(query, limit)
        
    def search_by_type(self, query: str, doc_type: str, limit: int = 5):
        """
        Realiza uma busca por documentos de um tipo específico.
        
        Args:
            query: Consulta de busca
            doc_type: Tipo de documento (text, pdf, video, image, json)
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes do tipo especificado
        """
        return self.search_service.search_by_type(query, doc_type, limit)
    
    def search_with_neural_ranking(self, query: str, user_id: str, limit: int = 5) -> List[Document]:
        """
        Realiza uma busca e reordena os resultados usando a rede neural.
        
        Args:
            query: Consulta de busca
            user_id: ID do usuário
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes ordenados pelo modelo neural
        """
        if not self.neural_network_service:
            return self.search(query, limit)
        
        docs = self.search(query, limit * 2)
        
        if not docs:
            return []
        
        try:
            ranked_docs = self.neural_network_service.predict_relevance(user_id, docs)
            
            return [doc for doc, _ in ranked_docs[:limit]]
        except Exception as e:
            print(f"Erro ao usar classificação neural: {e}")
            return docs[:limit]


if __name__ == '__main__':
    chroma_client = chromadb.Client()
    indexer = IndexerService(chroma_client)

    data_dir = "backend/resources"

    if indexer.index_data(data_dir):
        print("\nRealizando busca de exemplo...")
        results = indexer.search("educação", limit=2)
        print(f"Resultados para 'educação': {len(results)} documentos encontrados.") 