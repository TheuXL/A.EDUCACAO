from typing import List, Optional
from pathlib import Path

from ...domain.interfaces.document_parser import DocumentParser
from ...domain.interfaces.transcription_service import TranscriptionService
from ...domain.interfaces.ocr_service import OCRService
from .text_parser import TextParser
from .pdf_parser import PdfParser
from .json_parser import JsonParser
from .video_parser import VideoParser
from .image_parser import ImageParser
from .audio_parser import AudioParser


class ParserRegistry:
    """
    Gerencia todos os parsers disponíveis no sistema.
    Facilita o registro de novos parsers e a seleção do parser adequado para cada tipo de arquivo.
    """
    
    def __init__(
        self, 
        transcription_service: Optional[TranscriptionService] = None,
        ocr_service: Optional[OCRService] = None
    ):
        """
        Inicializa o registro com os parsers padrão.
        
        Args:
            transcription_service: Serviço de transcrição para vídeos e áudios (opcional)
            ocr_service: Serviço de OCR para imagens (opcional)
        """
        self._parsers: List[DocumentParser] = [
            TextParser(),
            PdfParser(),
            JsonParser(),
        ]
        
        # Adiciona o parser de vídeo se o serviço de transcrição for fornecido
        if transcription_service:
            self._parsers.append(VideoParser(transcription_service))
            self._parsers.append(AudioParser(transcription_service))
            
        # Adiciona o parser de imagem se o serviço de OCR for fornecido
        if ocr_service:
            self._parsers.append(ImageParser(ocr_service))
        
    def get_all_parsers(self) -> List[DocumentParser]:
        """
        Retorna todos os parsers registrados.
        
        Returns:
            Lista de todos os parsers
        """
        return self._parsers
        
    def register_parser(self, parser: DocumentParser) -> None:
        """
        Registra um novo parser.
        
        Args:
            parser: O parser a ser registrado
        """
        self._parsers.append(parser)
        
    def get_parser_for_file(self, file_path: Path) -> Optional[DocumentParser]:
        """
        Encontra o parser adequado para o tipo de arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Parser compatível ou None se nenhum parser suportar o tipo de arquivo
        """
        extension = file_path.suffix.lstrip('.')
        for parser in self._parsers:
            if parser.supports_extension(extension):
                return parser
        return None 