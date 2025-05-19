from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class TranscriptionService(ABC):
    """
    Interface para o serviço de transcrição de vídeos.
    Define o contrato para todas as implementações de transcrição.
    """
    
    @abstractmethod
    def transcribe_video(
        self, 
        video_path: str,
        language: str = "pt",
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Transcreve um vídeo para texto.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            language: Código do idioma (padrão: 'pt' para português)
            output_format: Formato de saída ('text', 'json', 'srt', etc.)
            
        Returns:
            Dicionário com o texto transcrito e metadados
        """
        pass
    
    @abstractmethod
    def transcribe_audio(
        self, 
        audio_path: str,
        language: str = "pt",
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Transcreve um arquivo de áudio.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            language: Código de idioma (default: 'pt' para português)
            output_format: Formato de saída ('text', 'json', etc.)
        
        Returns:
            Dicionário com a transcrição e metadados como timestamps
        """
        pass
    
    @abstractmethod
    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extrai o áudio de um vídeo para facilitar a transcrição.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            output_path: Caminho para salvar o arquivo de áudio (opcional)
            
        Returns:
            Caminho para o arquivo de áudio extraído
        """
        pass 