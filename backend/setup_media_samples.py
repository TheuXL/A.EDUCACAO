#!/usr/bin/env python3
"""
Script para processar os recursos reais e configurar a estrutura de diretórios para o backend.
Este script processa arquivos de texto, PDF, vídeo, áudio, JSON e imagens da pasta resources.
"""

import os
import shutil
import json
from pathlib import Path
import sys

# Verifica se existem bibliotecas necessárias
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("AVISO: pytesseract não encontrado. O OCR de imagens não estará disponível.")

# Corrigindo a verificação do MoviePy
HAS_MOVIEPY = False
try:
    import moviepy
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    print("AVISO: MoviePy não encontrado. A extração de áudio de vídeos não estará disponível.")

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("AVISO: OpenAI Whisper não encontrado. A transcrição de áudio não estará disponível.")

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("AVISO: PyMuPDF não encontrado. A extração de texto de PDFs não estará disponível.")


def create_directory_structure():
    """Cria a estrutura de diretórios necessária para o backend."""
    base_dir = Path(__file__).parent
    
    # Diretórios principais
    processed_data_dir = base_dir / "processed_data"
    text_dir = processed_data_dir / "text"
    audio_dir = processed_data_dir / "audio"
    transcripts_dir = processed_data_dir / "transcripts"
    embeddings_dir = processed_data_dir / "embeddings"
    chroma_db_dir = base_dir / "database" / "chromadb"
    
    # Cria todos os diretórios necessários
    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)
    os.makedirs(embeddings_dir, exist_ok=True)
    os.makedirs(chroma_db_dir, exist_ok=True)
    
    return {
        "base": base_dir,
        "processed_data": processed_data_dir,
        "text": text_dir,
        "audio": audio_dir,
        "transcripts": transcripts_dir,
        "embeddings": embeddings_dir,
        "chroma_db": chroma_db_dir
    }


def process_text_file(file_path, dirs):
    """
    Processa um arquivo de texto.
    
    Args:
        file_path: Caminho para o arquivo de texto
        dirs: Dicionário com os diretórios de destino
    
    Returns:
        Caminho para o arquivo processado
    """
    print(f"Processando arquivo de texto: {file_path}")
    
    # Lê o conteúdo do arquivo
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Tenta com outra codificação se utf-8 falhar
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Define o caminho de destino
    dest_file = dirs["text"] / file_path.name
    
    # Salva o conteúdo no diretório de textos processados
    with open(dest_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Arquivo de texto processado: {dest_file}")
    return dest_file


def process_pdf_file(file_path, dirs):
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        file_path: Caminho para o arquivo PDF
        dirs: Dicionário com os diretórios de destino
    
    Returns:
        Caminho para o arquivo de texto extraído
    """
    print(f"Processando arquivo PDF: {file_path}")
    
    if not HAS_PYMUPDF:
        print("AVISO: PyMuPDF não está disponível. Não é possível extrair texto do PDF.")
        return None
    
    try:
        # Abre o PDF
        pdf_document = fitz.open(file_path)
        text_content = ""
        
        # Extrai texto de cada página
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_content += page.get_text()
            text_content += f"\n\n--- Página {page_num + 1} ---\n\n"
        
        # Fecha o documento
        pdf_document.close()
        
        # Define o caminho de destino (converte para .txt)
        dest_file = dirs["text"] / f"{file_path.stem}.txt"
        
        # Salva o texto extraído
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"Texto extraído do PDF: {dest_file}")
        return dest_file
        
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return None


def process_video_file(file_path, dirs):
    """
    Extrai áudio de um arquivo de vídeo e transcreve.
    Se não for possível extrair o áudio, copia o vídeo para o diretório processado.
    
    Args:
        file_path: Caminho para o arquivo de vídeo
        dirs: Dicionário com os diretórios de destino
    
    Returns:
        Tuple com (caminho do áudio extraído, caminho da transcrição)
    """
    print(f"Processando arquivo de vídeo: {file_path}")
    
    # Cria um diretório para vídeos processados
    videos_dir = dirs["processed_data"] / "videos"
    os.makedirs(videos_dir, exist_ok=True)
    
    # Copia o vídeo original para o diretório de vídeos processados
    video_dest = videos_dir / file_path.name
    shutil.copy2(file_path, video_dest)
    print(f"Vídeo copiado para: {video_dest}")
    
    audio_file = None
    transcript_file = None
    
    if not HAS_MOVIEPY:
        print("AVISO: MoviePy não está disponível. Não é possível extrair áudio do vídeo.")
        # Cria um arquivo de texto simples com informações sobre o vídeo
        info_file = dirs["transcripts"] / f"{file_path.stem}_info.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Arquivo de vídeo: {file_path.name}\n")
            f.write(f"Caminho original: {file_path}\n")
            f.write(f"Caminho processado: {video_dest}\n")
            f.write("Não foi possível extrair áudio ou transcrição devido à falta de dependências.\n")
        
        return video_dest, info_file
    
    try:
        # Extrai o áudio do vídeo
        video = VideoFileClip(str(file_path))
        audio_file = dirs["audio"] / f"{file_path.stem}.mp3"
        video.audio.write_audiofile(str(audio_file))
        
        print(f"Áudio extraído do vídeo: {audio_file}")
        
        # Transcreve o áudio se o Whisper estiver disponível
        if HAS_WHISPER:
            try:
                print("Transcrevendo áudio...")
                model = whisper.load_model("base")
                result = model.transcribe(str(audio_file))
                
                # Salva a transcrição
                transcript_file = dirs["transcripts"] / f"{file_path.stem}_transcript.txt"
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(result["text"])
                
                # Salva os segmentos com timestamps
                segments_file = dirs["transcripts"] / f"{file_path.stem}_segments.json"
                with open(segments_file, 'w', encoding='utf-8') as f:
                    json.dump(result["segments"], f, indent=2)
                
                print(f"Transcrição concluída: {transcript_file}")
            except Exception as e:
                print(f"Erro na transcrição: {e}")
        else:
            print("AVISO: Whisper não está disponível. Não é possível transcrever o áudio.")
        
        return audio_file, transcript_file
        
    except Exception as e:
        print(f"Erro ao processar vídeo: {e}")
        return video_dest, None


def process_json_file(file_path, dirs):
    """
    Processa um arquivo JSON.
    
    Args:
        file_path: Caminho para o arquivo JSON
        dirs: Dicionário com os diretórios de destino
    
    Returns:
        Caminho para o arquivo de texto normalizado
    """
    print(f"Processando arquivo JSON: {file_path}")
    
    try:
        # Lê o conteúdo do JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Converte o JSON para texto formatado
        text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Define o caminho de destino (converte para .txt)
        dest_file = dirs["text"] / f"{file_path.stem}.txt"
        
        # Salva o texto normalizado
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"JSON normalizado: {dest_file}")
        return dest_file
        
    except Exception as e:
        print(f"Erro ao processar JSON: {e}")
        return None


def process_image_file(file_path, dirs):
    """
    Extrai texto de uma imagem usando OCR.
    
    Args:
        file_path: Caminho para o arquivo de imagem
        dirs: Dicionário com os diretórios de destino
    
    Returns:
        Caminho para o arquivo de texto extraído
    """
    print(f"Processando arquivo de imagem: {file_path}")
    
    if not HAS_OCR:
        print("AVISO: OCR não está disponível. Não é possível extrair texto da imagem.")
        return None
    
    try:
        # Abre a imagem
        image = Image.open(file_path)
        
        # Extrai texto com OCR
        text = pytesseract.image_to_string(image, lang='por')
        
        # Define o caminho de destino
        dest_file = dirs["transcripts"] / f"{file_path.stem}_ocr.txt"
        
        # Salva o texto extraído
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Texto extraído da imagem: {dest_file}")
        return dest_file
        
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        return None


def process_resources(resources_dir, dirs):
    """
    Processa todos os recursos da pasta especificada.
    
    Args:
        resources_dir: Caminho para o diretório de recursos
        dirs: Dicionário com os diretórios de destino
    
    Returns:
        Dicionário com os arquivos processados
    """
    processed_files = {
        "text": [],
        "pdf": [],
        "video": [],
        "audio": [],
        "json": [],
        "image": []
    }
    
    # Verifica se o diretório existe
    if not os.path.exists(resources_dir):
        print(f"ERRO: Diretório de recursos não encontrado: {resources_dir}")
        return processed_files
    
    # Processa cada arquivo no diretório
    for file_path in Path(resources_dir).glob("*"):
        if not file_path.is_file():
            continue
        
        extension = file_path.suffix.lower()
        
        # Processa de acordo com a extensão
        if extension in ['.txt', '.md', '.html', '.htm']:
            result = process_text_file(file_path, dirs)
            if result:
                processed_files["text"].append(result)
                
        elif extension == '.pdf':
            result = process_pdf_file(file_path, dirs)
            if result:
                processed_files["pdf"].append(result)
                
        elif extension in ['.mp4', '.avi', '.mov', '.mkv']:
            video_file, transcript_file = process_video_file(file_path, dirs)
            if video_file:
                processed_files["video"].append({
                    "original": file_path,
                    "processed": video_file,
                    "transcript": transcript_file
                })
                
        elif extension in ['.mp3', '.wav', '.ogg']:
            # Para arquivos de áudio, poderíamos transcrever diretamente
            # Mas por enquanto, apenas copiamos para o diretório de áudio
            dest_file = dirs["audio"] / file_path.name
            shutil.copy2(file_path, dest_file)
            processed_files["audio"].append(dest_file)
                
        elif extension == '.json':
            result = process_json_file(file_path, dirs)
            if result:
                processed_files["json"].append(result)
                
        elif extension in ['.jpg', '.jpeg', '.png', '.gif']:
            result = process_image_file(file_path, dirs)
            # Também copiamos a imagem original para referência
            images_dir = dirs["processed_data"] / "images"
            os.makedirs(images_dir, exist_ok=True)
            dest_file = images_dir / file_path.name
            shutil.copy2(file_path, dest_file)
            if result:
                processed_files["image"].append({
                    "original": file_path,
                    "processed": dest_file,
                    "ocr": result
                })
    
    return processed_files


def main():
    """Função principal que processa os recursos."""
    print("Configurando estrutura de diretórios para o backend...")
    
    # Cria a estrutura de diretórios
    dirs = create_directory_structure()
    
    # Caminho para os recursos
    resources_dir = os.path.join(dirs["base"], "resources")
    
    # Processa os recursos
    print(f"\nProcessando recursos de: {resources_dir}")
    processed_files = process_resources(resources_dir, dirs)
    
    # Resumo dos arquivos processados
    print("\nResumo dos arquivos processados:")
    for file_type, files in processed_files.items():
        print(f"{file_type.upper()}: {len(files)} arquivos")
    
    print("\nEstrutura de diretórios criada:")
    for dir_name, dir_path in dirs.items():
        print(f"{dir_name}: {dir_path}")
    
    print("\nProcessamento concluído!")
    print("Agora você pode iniciar o backend para indexar os arquivos processados.")


if __name__ == "__main__":
    main() 