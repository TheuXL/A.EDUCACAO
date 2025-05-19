import os
from pathlib import Path
from typing import Dict, Any, Optional, Set

from ...domain.entities.document import Document, DocumentType
from ...domain.interfaces.document_parser import DocumentParser
from ...domain.interfaces.transcription_service import TranscriptionService


class VideoParser(DocumentParser):
    """
    Parser para arquivos de vídeo.
    Utiliza um serviço de transcrição para extrair o conteúdo.
    """
    
    def __init__(self, transcription_service: TranscriptionService):
        """
        Inicializa o parser de vídeo.
        
        Args:
            transcription_service: Serviço para transcrição de vídeos
        """
        self.transcription_service = transcription_service
        
    def supports_extension(self, extension: str) -> bool:
        """
        Verifica se o parser suporta a extensão do arquivo.
        
        Args:
            extension: Extensão do arquivo (sem o ponto)
            
        Returns:
            True se o parser suportar a extensão, False caso contrário
        """
        supported_extensions = {"mp4", "avi", "mov", "mkv", "webm", "m4v", "mpg", "mpeg"}
        return extension.lower() in supported_extensions
    
    def get_supported_extensions(self) -> Set[str]:
        """
        Retorna a lista de extensões suportadas pelo parser.
        
        Returns:
            Conjunto com as extensões suportadas
        """
        return {"mp4", "avi", "mov", "mkv", "webm", "m4v", "mpg", "mpeg"}
    
    def parse(self, file_path: Path) -> Document:
        """
        Converte um arquivo de vídeo em um documento.
        
        Args:
            file_path: Caminho para o arquivo de vídeo
            
        Returns:
            Documento com o conteúdo e metadados do vídeo
        """
        # Verifica se o arquivo existe
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        # Obtém o caminho absoluto
        absolute_path = str(file_path.absolute())
        
        # Transcreve o vídeo
        try:
            transcription_result = self.transcription_service.transcribe_video(
                video_path=absolute_path,
                language="pt",
                output_format="text"
            )
            
            # Extrai o conteúdo transcrito
            content = transcription_result["text"]
            
            # Extrai metadados
            metadata = self._extract_metadata(file_path, transcription_result)
            
            # Cria e retorna o documento
            return Document(
                id=file_path.name,
                content=content,
                doc_type=DocumentType.VIDEO,
                metadata=metadata
            )
            
        except Exception as e:
            raise ValueError(f"Erro ao transcrever o vídeo {file_path.name}: {str(e)}")
    
    def _extract_metadata(
        self, 
        file_path: Path, 
        transcription_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrai metadados do arquivo de vídeo.
        
        Args:
            file_path: Caminho para o arquivo de vídeo
            transcription_result: Resultado da transcrição
            
        Returns:
            Dicionário com os metadados
        """
        # Obtém informações básicas do arquivo
        file_stat = file_path.stat()
        
        # Metadados básicos
        metadata = {
            "source": str(file_path.absolute()),
            "size_bytes": file_stat.st_size,
            "created_at": file_stat.st_ctime,
            "modified_at": file_stat.st_mtime,
            "extension": file_path.suffix.lstrip('.'),
            "title": file_path.stem
        }
        
        # Adiciona metadados da transcrição
        if "language" in transcription_result:
            metadata["language"] = transcription_result["language"]
            
        if "segments" in transcription_result:
            # Adiciona informações sobre os segmentos de tempo
            segments = transcription_result["segments"]
            if segments:
                # Calcula a duração aproximada com base no último segmento
                last_segment = segments[-1]
                if "end" in last_segment:
                    metadata["duration_seconds"] = last_segment["end"]
                    
                # Adiciona timestamps dos segmentos
                metadata["timestamps"] = [
                    {
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                        "text": segment.get("text", "")
                    }
                    for segment in segments
                ]
                
        return metadata 