from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class OCRService(ABC):
    """
    Interface para o serviço de reconhecimento óptico de caracteres (OCR).
    Define o contrato para todas as implementações de OCR.
    """
    
    @abstractmethod
    def extract_text(
        self, 
        image_path: str,
        language: str = "por", 
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extrai texto de uma imagem.
        
        Args:
            image_path: Caminho para a imagem
            language: Código do idioma (padrão: 'por' para português)
            preprocess: Se True, aplica pré-processamento para melhorar a extração
            
        Returns:
            Dicionário com o texto extraído e metadados
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def detect_tables(
        self,
        image_path: str,
        extract_data: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Detecta e opcionalmente extrai dados de tabelas na imagem.
        
        Args:
            image_path: Caminho para a imagem
            extract_data: Se True, extrai os dados das tabelas detectadas
            
        Returns:
            Lista de dicionários com os dados das tabelas ou None se nenhuma tabela for detectada
        """
        pass 