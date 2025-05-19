"""
Serviço de OCR para extrair texto de imagens.
Este serviço usa o Tesseract OCR para processamento de imagens.
"""

from typing import Optional, List, Dict, Any
import os
from pathlib import Path
import cv2
import numpy as np

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class TesseractOCRService:
    """
    Implementação do serviço OCR usando Tesseract.
    Se o Tesseract não estiver disponível, usa um modo de fallback.
    """
    
    def __init__(self):
        self.is_available = TESSERACT_AVAILABLE
        # Diretório para armazenar resultados de OCR
        self.output_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / "processed_data" / "text"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_text(self, image_path: str) -> Optional[str]:
        """
        Extrai texto de uma imagem usando OCR.
        
        Args:
            image_path: Caminho para o arquivo de imagem
            
        Returns:
            String contendo o texto extraído ou None se ocorrer erro
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(image_path):
                print(f"Arquivo não encontrado: {image_path}")
                return None
                
            # Se o Tesseract estiver disponível, usa-o para extrair texto
            if self.is_available:
                # Lê a imagem com OpenCV
                image = cv2.imread(image_path)
                if image is None:
                    print(f"Não foi possível ler a imagem: {image_path}")
                    return None
                
                # Converte para escala de cinza para melhor OCR
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Aplica um leve desfoque para remover ruído
                gray = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # Aplica limiarização adaptativa
                thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
                
                # Extrai texto usando pytesseract
                text = pytesseract.image_to_string(thresh, lang='por')
                
                # Salva o texto extraído
                output_file = self.output_dir / f"{Path(image_path).stem}_ocr.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                return text
            else:
                # Fallback: tenta ler um arquivo de texto associado se existir
                txt_path = Path(image_path).with_suffix('.txt')
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        return f.read()
                
                # Se não encontrar arquivo de texto, retorna um texto genérico
                return f"[Conteúdo da imagem {os.path.basename(image_path)}] - OCR não disponível"
                
        except Exception as e:
            print(f"Erro ao extrair texto da imagem: {str(e)}")
            return None
    
    def extract_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extrai metadados da imagem.
        
        Args:
            image_path: Caminho para o arquivo de imagem
            
        Returns:
            Dicionário contendo metadados da imagem
        """
        metadata = {
            "source": image_path,
            "is_processed": self.is_available
        }
        
        try:
            # Tenta extrair dimensões da imagem
            if os.path.exists(image_path):
                img = cv2.imread(image_path)
                if img is not None:
                    height, width, channels = img.shape
                    metadata.update({
                        "width": width,
                        "height": height,
                        "channels": channels,
                        "format": os.path.splitext(image_path)[1][1:].upper()
                    })
        except Exception as e:
            print(f"Erro ao extrair metadados da imagem: {str(e)}")
            
        return metadata
    
    def is_functional(self) -> bool:
        """
        Verifica se o serviço de OCR está funcional.
        
        Returns:
            True se o serviço estiver disponível, False caso contrário
        """
        return self.is_available 