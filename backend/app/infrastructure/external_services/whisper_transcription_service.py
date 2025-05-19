import os
import tempfile
from typing import Dict, Any, Optional
import subprocess
import json
from pathlib import Path

from ...domain.interfaces.transcription_service import TranscriptionService


class WhisperTranscriptionService(TranscriptionService):
    """
    Implementação do serviço de transcrição de vídeos utilizando o modelo Whisper.
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Inicializa o serviço de transcrição com Whisper.
        
        Args:
            model_size: Tamanho do modelo Whisper ('tiny', 'base', 'small', 'medium', 'large')
            device: Dispositivo para execução ('cpu' ou 'cuda')
        """
        self.model_size = model_size
        self.device = device
        self.temp_dir = None
        
        # Verifica se o Whisper está instalado
        try:
            import whisper
            self.whisper = whisper
            self._model = None
        except ImportError:
            raise ImportError(
                "Whisper não está instalado. Instale com: pip install openai-whisper"
            )
    
    def _load_model(self):
        """
        Carrega o modelo Whisper sob demanda.
        """
        if self._model is None:
            self._model = self.whisper.load_model(self.model_size, device=self.device)
    
    def transcribe_video(
        self, 
        video_path: str,
        language: str = "pt",
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Transcreve o áudio de um vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            language: Código de idioma (default: 'pt' para português)
            output_format: Formato de saída ('text', 'json', etc.)
        
        Returns:
            Dicionário com a transcrição e metadados como timestamps
        """
        try:
            # Extrai o áudio do vídeo
            audio_path = self.extract_audio(video_path)
            
            # Transcreve o áudio extraído
            return self.transcribe_audio(audio_path, language, output_format)
            
        except Exception as e:
            print(f"Erro ao transcrever vídeo {video_path}: {e}")
            return {"error": str(e), "text": ""}
    
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
        try:
            # Certifica-se de que o modelo está carregado
            self._load_model()
            
            # Realiza a transcrição
            result = self._model.transcribe(
                audio_path,
                language=language,
                fp16=self.device == "cuda"
            )
            
            # Salva a saída em um arquivo JSON, se solicitado
            if output_format == "json":
                json_output_path = os.path.splitext(audio_path)[0] + "_transcription.json"
                self._save_transcription(result, json_output_path, "json")
            
            # Formata e retorna o resultado
            return {
                "text": result["text"],
                "segments": result["segments"],
                "language": result.get("language", language),
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            print(f"Erro ao transcrever áudio {audio_path}: {e}")
            return {"error": str(e), "text": ""}
    
    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extrai o áudio de um vídeo usando FFmpeg.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            output_path: Caminho para salvar o arquivo de áudio
            
        Returns:
            Caminho para o arquivo de áudio extraído
        """
        # Se não for fornecido um caminho de saída, usa um arquivo temporário
        if output_path is None:
            # Cria o diretório temporário se ainda não existir
            if self.temp_dir is None:
                self.temp_dir = tempfile.mkdtemp()
                
            # Cria um nome de arquivo temporário com a extensão .wav
            output_path = os.path.join(
                self.temp_dir, 
                os.path.basename(os.path.splitext(video_path)[0]) + ".wav"
            )
        
        # Executa o FFmpeg para extrair o áudio
        try:
            subprocess.run(
                [
                    "ffmpeg", 
                    "-i", video_path, 
                    "-ar", "16000", 
                    "-ac", "1", 
                    "-c:a", "pcm_s16le", 
                    output_path
                ],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erro ao extrair áudio: {e.stderr.decode('utf-8')}")
        except FileNotFoundError:
            raise FileNotFoundError(
                "FFmpeg não está instalado. Instale o FFmpeg para extrair áudio de vídeos."
            )
            
        return output_path
    
    def _save_transcription(
        self,
        result: Dict[str, Any],
        output_path: str,
        format: str = "json"
    ) -> None:
        """
        Salva a transcrição em um formato específico.
        
        Args:
            result: Resultado da transcrição
            output_path: Caminho para salvar o arquivo
            format: Formato de saída ('json', 'srt', 'vtt', etc.)
        """
        # Verifica se o diretório de saída existe
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        elif format == "srt":
            self.whisper.utils.write_srt(result["segments"], output_path)
        elif format == "vtt":
            self.whisper.utils.write_vtt(result["segments"], output_path)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["text"])
    
    def __del__(self):
        """
        Limpa os arquivos temporários ao destruir o objeto.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True) 