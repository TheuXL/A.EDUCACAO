"""
Serviço de transcrição de áudio e vídeo usando o modelo Whisper da OpenAI.
"""

from typing import Optional, Dict, Any
import os
import json
import tempfile
from pathlib import Path
import subprocess

try:
    import whisper
    import torch
    import ffmpeg
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class WhisperTranscriptionService:
    """
    Serviço de transcrição que utiliza o modelo Whisper da OpenAI.
    Se o Whisper não estiver disponível, usa um modo de fallback.
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Inicializa o serviço de transcrição.
        
        Args:
            model_size: Tamanho do modelo Whisper ("tiny", "base", "small", "medium", "large")
            device: Dispositivo para processamento ("cpu" ou "cuda")
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self.is_available = WHISPER_AVAILABLE
        
        # Diretórios para armazenar resultados
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.audio_dir = self.base_dir / "processed_data" / "audio"
        self.transcript_dir = self.base_dir / "processed_data" / "transcripts"
        
        # Cria os diretórios se não existirem
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.transcript_dir, exist_ok=True)
        
        # Carrega o modelo se disponível
        if self.is_available:
            try:
                self._load_model()
                print(f"Modelo Whisper '{model_size}' carregado com sucesso no dispositivo '{device}'")
            except Exception as e:
                print(f"Erro ao carregar o modelo Whisper: {e}")
                self.is_available = False
    
    def _load_model(self):
        """Carrega o modelo Whisper."""
        if not self.model and self.is_available:
            self.model = whisper.load_model(self.model_size, device=self.device)
    
    def transcribe_video(self, 
        video_path: str,
        language: str = "pt",
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Transcreve um arquivo de vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            language: Código do idioma (pt, en, etc.)
            output_format: Formato de saída (text, json, vtt, srt)
            
        Returns:
            Dicionário com a transcrição e metadados
        """
        # Extrai o áudio do vídeo
        audio_path = self.extract_audio(video_path)
        
        # Transcreve o áudio extraído
        result = self.transcribe_audio(audio_path, language, output_format)
        
        # Adiciona o caminho do vídeo original aos metadados
        if "metadata" in result:
            result["metadata"]["video_source"] = video_path
        
        return result
    
    def transcribe_audio(self, 
        audio_path: str,
        language: str = "pt",
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        Transcreve um arquivo de áudio.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            language: Código do idioma (pt, en, etc.)
            output_format: Formato de saída (text, json, vtt, srt)
            
        Returns:
            Dicionário com a transcrição e metadados
        """
        # Verifica se o arquivo existe
        if not os.path.exists(audio_path):
            return {
                "error": f"Arquivo não encontrado: {audio_path}",
                "text": "",
                "metadata": {"error": "file_not_found"}
            }
        
        # Caminho para salvar a transcrição
        output_base = self.transcript_dir / Path(audio_path).stem
        
        # Se o Whisper estiver disponível, realiza a transcrição
        if self.is_available:
            try:
                # Carrega o modelo se ainda não foi carregado
                if not self.model:
                    self._load_model()
                
                # Realiza a transcrição
                result = self.model.transcribe(
                    audio_path,
                    language=language,
                    verbose=False
                )
                
                # Extrai o texto e os segmentos
                text = result["text"]
                segments = result["segments"]
                
                # Salva a transcrição em diferentes formatos
                output_json = f"{output_base}.json"
                output_txt = f"{output_base}.txt"
                
                # Salva o texto simples
                with open(output_txt, "w", encoding="utf-8") as f:
                    f.write(text)
                
                # Salva o JSON completo
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                # Prepara os timestamps para metadados
                timestamps = []
                for segment in segments:
                    timestamps.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"]
                    })
                
                return {
                    "text": text,
                    "segments": segments,
                    "metadata": {
                        "source": audio_path,
                        "language": language,
                        "timestamps": timestamps,
                        "duration_seconds": segments[-1]["end"] if segments else 0,
                        "transcript_file": str(output_txt)
                    }
                }
                
            except Exception as e:
                print(f"Erro ao transcrever áudio: {e}")
                # Fallback para modo alternativo
                pass
        
        # Modo alternativo: tenta ler um arquivo de transcrição existente
        txt_path = Path(audio_path).with_suffix('.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
                return {
                    "text": text,
                    "metadata": {
                        "source": audio_path,
                        "language": language,
                        "note": "Transcrição de arquivo existente (não processado por Whisper)"
                    }
                }
        
        # Se tudo falhar, retorna uma mensagem indicando que a transcrição não está disponível
        return {
            "text": f"[Conteúdo do áudio {os.path.basename(audio_path)}] - Transcrição não disponível",
            "metadata": {
                "source": audio_path,
                "error": "transcription_unavailable"
            }
        }
    
    def extract_audio(self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extrai o áudio de um arquivo de vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            output_path: Caminho para salvar o áudio extraído (opcional)
            
        Returns:
            Caminho para o arquivo de áudio extraído
        """
        # Define o caminho de saída se não for fornecido
        if not output_path:
            output_path = str(self.audio_dir / f"{Path(video_path).stem}.mp3")
        
        try:
            # Verifica se o arquivo já existe
            if os.path.exists(output_path):
                return output_path
            
            # Tenta usar ffmpeg-python se disponível
            if 'ffmpeg' in globals():
                try:
                    (
                        ffmpeg
                        .input(video_path)
                        .output(output_path, acodec='libmp3lame', ac=1, ar='16k')
                        .overwrite_output()
                        .run(quiet=True, capture_stdout=True, capture_stderr=True)
                    )
                    return output_path
                except Exception as e:
                    print(f"Erro ao usar ffmpeg-python: {e}")
                    # Continua para o método alternativo
            
            # Método alternativo: usa o subprocess para chamar ffmpeg
            try:
                subprocess.run(
                    [
                        "ffmpeg", "-i", video_path, 
                        "-vn", "-acodec", "libmp3lame", 
                        "-ac", "1", "-ar", "16000", 
                        "-f", "mp3", output_path
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return output_path
            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar ffmpeg: {e}")
                
                # Se o ffmpeg falhar, tenta copiar um arquivo de áudio existente
                mp3_path = Path(video_path).with_suffix('.mp3')
                if os.path.exists(mp3_path):
                    import shutil
                    shutil.copy(mp3_path, output_path)
                    return output_path
        except Exception as e:
            print(f"Erro ao extrair áudio: {e}")
        
        # Se tudo falhar, retorna o caminho do vídeo original
        return video_path
    
    def _save_transcription(self,
        result: Dict[str, Any],
        output_path: str,
        format: str = "json"
    ) -> None:
        """
        Salva a transcrição em um arquivo.
        
        Args:
            result: Resultado da transcrição
            output_path: Caminho para salvar o arquivo
            format: Formato de saída (json, text)
        """
        try:
            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            elif format == "text":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result["text"])
            else:
                print(f"Formato não suportado: {format}")
        except Exception as e:
            print(f"Erro ao salvar transcrição: {e}")
    
    def is_functional(self) -> bool:
        """
        Verifica se o serviço está funcional.
        
        Returns:
            True se o serviço estiver disponível, False caso contrário
        """
        return self.is_available
    
    def __del__(self):
        """Liberação de recursos quando o objeto é destruído."""
        # Libera o modelo da GPU se estiver usando CUDA
        if self.model and self.device == "cuda":
            try:
                del self.model
                torch.cuda.empty_cache()
            except:
                pass 