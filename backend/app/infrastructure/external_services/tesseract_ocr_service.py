import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from ...domain.interfaces.ocr_service import OCRService


class TesseractOCRService(OCRService):
    """
    Implementação do serviço de OCR utilizando o Tesseract.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o serviço de OCR com Tesseract.
        
        Args:
            config: Configurações opcionais para o Tesseract
        """
        self.config = config or {}
        
        # Verifica se o pytesseract está instalado
        try:
            import pytesseract
            self.tesseract = pytesseract
            
            # Define o caminho para o executável do Tesseract, se fornecido na configuração
            if "tesseract_cmd" in self.config:
                self.tesseract.pytesseract.tesseract_cmd = self.config["tesseract_cmd"]
        except ImportError:
            raise ImportError(
                "Pytesseract não está instalado. Instale com: pip install pytesseract"
            )
            
        # Verifica se o OpenCV está instalado
        try:
            import cv2
            self.cv2 = cv2
        except ImportError:
            raise ImportError(
                "OpenCV não está instalado. Instale com: pip install opencv-python"
            )
    
    def extract_text(
        self, 
        image_path: str,
        language: str = "por", 
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extrai texto de uma imagem usando o Tesseract.
        
        Args:
            image_path: Caminho para a imagem
            language: Código do idioma (padrão: 'por' para português)
            preprocess: Se True, aplica pré-processamento para melhorar a extração
            
        Returns:
            Dicionário com o texto extraído e metadados
        """
        # Verifica se o arquivo existe
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
            
        # Carrega a imagem
        image = self.cv2.imread(image_path)
        
        # Aplica pré-processamento, se solicitado
        if preprocess:
            image = self._preprocess_image(image)
            
        # Extrai o texto
        text = self.tesseract.image_to_string(image, lang=language)
        
        # Extrai informações adicionais
        data = self.tesseract.image_to_data(image, lang=language, output_type=self.tesseract.Output.DICT)
        
        # Prepara a resposta
        response = {
            "text": text,
            "language": language,
            "source_path": image_path,
            "words": data["text"],
            "confidences": data["conf"],
            "word_boxes": [
                {
                    "text": data["text"][i],
                    "confidence": data["conf"][i],
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "line_num": data["line_num"][i],
                    "block_num": data["block_num"][i]
                }
                for i in range(len(data["text"]))
                if data["text"][i].strip() and data["conf"][i] > 30  # Filtra resultados vazios e de baixa confiança
            ]
        }
            
        return response
    
    def extract_text_from_regions(
        self,
        image_path: str,
        regions: List[Dict[str, int]],
        language: str = "por"
    ) -> Dict[str, Any]:
        """
        Extrai texto de regiões específicas da imagem.
        
        Args:
            image_path: Caminho para a imagem
            regions: Lista de dicionários com as coordenadas das regiões
                     (ex: [{'x': 0, 'y': 0, 'width': 100, 'height': 100}])
            language: Código do idioma
            
        Returns:
            Dicionário com o texto extraído por região e metadados
        """
        # Verifica se o arquivo existe
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
            
        # Carrega a imagem
        image = self.cv2.imread(image_path)
        
        # Extrai texto de cada região
        region_results = []
        
        for i, region in enumerate(regions):
            # Extrai a região da imagem
            x, y, width, height = region["x"], region["y"], region["width"], region["height"]
            roi = image[y:y+height, x:x+width]
            
            # Verifica se a região é válida
            if roi.size == 0:
                continue
                
            # Aplica pré-processamento na região
            roi = self._preprocess_image(roi)
            
            # Extrai o texto da região
            text = self.tesseract.image_to_string(roi, lang=language)
            
            # Adiciona o resultado
            region_results.append({
                "region_id": i,
                "coordinates": region,
                "text": text
            })
            
        # Prepara a resposta
        response = {
            "source_path": image_path,
            "language": language,
            "region_count": len(region_results),
            "regions": region_results
        }
            
        return response
    
    def detect_tables(
        self,
        image_path: str,
        extract_data: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Detecta e opcionalmente extrai dados de tabelas na imagem.
        Para detecção de tabelas, usa uma combinação de detecção de linhas e análise de estrutura.
        
        Args:
            image_path: Caminho para a imagem
            extract_data: Se True, extrai os dados das tabelas detectadas
            
        Returns:
            Lista de dicionários com os dados das tabelas ou None se nenhuma tabela for detectada
        """
        # Verifica se o arquivo existe
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
            
        # Carrega a imagem
        image = self.cv2.imread(image_path)
        gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
        
        # Binariza a imagem
        _, binary = self.cv2.threshold(gray, 150, 255, self.cv2.THRESH_BINARY_INV)
        
        # Detecta linhas horizontais e verticais
        horizontal_kernel = self.cv2.getStructuringElement(self.cv2.MORPH_RECT, (50, 1))
        horizontal_lines = self.cv2.morphologyEx(binary, self.cv2.MORPH_OPEN, horizontal_kernel)
        
        vertical_kernel = self.cv2.getStructuringElement(self.cv2.MORPH_RECT, (1, 50))
        vertical_lines = self.cv2.morphologyEx(binary, self.cv2.MORPH_OPEN, vertical_kernel)
        
        # Combina linhas horizontais e verticais
        table_mask = horizontal_lines + vertical_lines
        
        # Detecta contornos, que podem ser tabelas
        contours, _ = self.cv2.findContours(table_mask, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtra contornos para encontrar retângulos de tamanho razoável (potenciais tabelas)
        table_contours = []
        for contour in contours:
            x, y, w, h = self.cv2.boundingRect(contour)
            if w > 100 and h > 100:  # Ignore contornos muito pequenos
                table_contours.append((x, y, w, h))
                
        if not table_contours:
            return None
            
        # Resultados da detecção
        tables = []
        
        for i, (x, y, w, h) in enumerate(table_contours):
            table_roi = image[y:y+h, x:x+w]
            
            table_info = {
                "table_id": i,
                "coordinates": {"x": x, "y": y, "width": w, "height": h}
            }
            
            # Se solicitado, extrai os dados da tabela
            if extract_data:
                # Usa o Tesseract com configuração específica para tabelas
                table_data = self.tesseract.image_to_data(
                    table_roi, 
                    lang="por",
                    config="--psm 6",  # Assume um único bloco uniforme de texto
                    output_type=self.tesseract.Output.DICT
                )
                
                # Organiza os dados extraídos
                table_info["data"] = self._organize_table_data(table_data)
                
            tables.append(table_info)
            
        return tables
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica técnicas de pré-processamento para melhorar a extração de texto.
        
        Args:
            image: Imagem a ser processada (array NumPy)
            
        Returns:
            Imagem processada
        """
        # Converte para escala de cinza
        if len(image.shape) == 3:
            gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Aplica redução de ruído
        denoised = self.cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Aplica threshold adaptativo
        threshold = self.cv2.adaptiveThreshold(
            denoised, 255, self.cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            self.cv2.THRESH_BINARY, 11, 2
        )
        
        # Aplica dilatação e erosão para remover ruído
        kernel = np.ones((1, 1), np.uint8)
        opening = self.cv2.morphologyEx(threshold, self.cv2.MORPH_OPEN, kernel)
        
        return opening
    
    def _organize_table_data(self, raw_data: Dict[str, Any]) -> List[List[str]]:
        """
        Organiza os dados extraídos em formato de tabela.
        
        Args:
            raw_data: Dados brutos extraídos pelo Tesseract
            
        Returns:
            Lista de linhas, onde cada linha é uma lista de strings (células)
        """
        # Agrupar por número de linha
        lines = {}
        for i in range(len(raw_data["text"])):
            if raw_data["text"][i].strip():  # Ignora células vazias
                line_num = raw_data["line_num"][i]
                if line_num not in lines:
                    lines[line_num] = []
                
                lines[line_num].append({
                    "text": raw_data["text"][i],
                    "left": raw_data["left"][i],
                    "conf": raw_data["conf"][i]
                })
        
        # Ordena as células de cada linha da esquerda para a direita
        for line_num in lines:
            lines[line_num].sort(key=lambda x: x["left"])
        
        # Constrói a matriz de dados da tabela
        table_data = []
        for line_num in sorted(lines.keys()):
            row = [cell["text"] for cell in lines[line_num]]
            table_data.append(row)
            
        return table_data 