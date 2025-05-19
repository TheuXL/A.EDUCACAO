import os
from pathlib import Path
from typing import Dict, Any, Optional, Set

from ...domain.entities.document import Document, DocumentType
from ...domain.interfaces.document_parser import DocumentParser
from ...domain.interfaces.transcription_service import TranscriptionService


class AudioParser(DocumentParser):
    """
    Parser para arquivos de áudio.
    Utiliza um serviço de transcrição para extrair o conteúdo textual.
    """
    
    def __init__(self, transcription_service: TranscriptionService):
        """
        Inicializa o parser de áudio.
        
        Args:
            transcription_service: Serviço para transcrição de áudio
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
        supported_extensions = {"mp3", "wav", "ogg", "aac", "flac", "m4a"}
        return extension.lower() in supported_extensions
    
    def get_supported_extensions(self) -> Set[str]:
        """
        Retorna a lista de extensões suportadas pelo parser.
        
        Returns:
            Conjunto com as extensões suportadas
        """
        return {"mp3", "wav", "ogg", "aac", "flac", "m4a"}
    
    def parse(self, file_path: Path) -> Document:
        """
        Processa um arquivo de áudio.
        
        Args:
            file_path: Caminho para o arquivo de áudio
            
        Returns:
            Document com o conteúdo processado
        """
        try:
            # Transcreve o áudio
            result = self.transcription_service.transcribe_audio(file_path.as_posix())
            
            # Extrai o texto da transcrição
            if isinstance(result, dict):
                text = result.get('text', '')
                segments = result.get('segments', [])
            else:
                text = str(result)
                segments = []
            
            # Metadados do áudio
            metadata = self._extract_metadata(file_path, result)
            
            # Cria o documento
            return Document(
                id=file_path.name,
                content=text,
                doc_type=DocumentType.AUDIO,
                metadata=metadata
            )
            
        except Exception as e:
            # Se houver erro na transcrição, cria um documento com conteúdo vazio
            # mas mantém a referência ao áudio
            metadata = self._extract_metadata(file_path, error=str(e))
            
            return Document(
                id=file_path.name,
                content="",
                doc_type=DocumentType.AUDIO,
                metadata=metadata
            )
    
    def _extract_metadata(
        self, 
        file_path: Path, 
        transcription_result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extrai metadados do arquivo de áudio.
        
        Args:
            file_path: Caminho para o arquivo de áudio
            transcription_result: Resultado da transcrição (opcional)
            error: Mensagem de erro, se houver (opcional)
            
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
            "type": "audio",
            "title": file_path.stem,
        }
        
        # Adiciona informações da transcrição, se disponíveis
        if transcription_result and isinstance(transcription_result, dict):
            if "duration" in transcription_result:
                metadata["duration_seconds"] = transcription_result["duration"]
                
            if "segments" in transcription_result:
                # Adiciona timestamps dos segmentos de fala
                metadata["timestamps"] = [
                    {
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                        "text": segment.get("text", "")
                    }
                    for segment in transcription_result["segments"]
                ]
                
            if "language" in transcription_result:
                metadata["language"] = transcription_result["language"]
        
        # Adiciona informação de erro, se houver
        if error:
            metadata["error"] = error
            
        return metadata 