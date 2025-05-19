import os
from pathlib import Path
from typing import Dict, Any, Optional, Set

from ...domain.entities.document import Document, DocumentType
from ...domain.interfaces.document_parser import DocumentParser
from ...domain.interfaces.ocr_service import OCRService


class ImageParser(DocumentParser):
    """
    Parser para arquivos de imagem.
    Utiliza um serviço de OCR para extrair o texto.
    """
    
    def __init__(self, ocr_service: OCRService):
        """
        Inicializa o parser de imagem.
        
        Args:
            ocr_service: Serviço para reconhecimento óptico de caracteres
        """
        self.ocr_service = ocr_service
        
    def supports_extension(self, extension: str) -> bool:
        """
        Verifica se o parser suporta a extensão do arquivo.
        
        Args:
            extension: Extensão do arquivo (sem o ponto)
            
        Returns:
            True se o parser suportar a extensão, False caso contrário
        """
        supported_extensions = {"jpg", "jpeg", "png", "bmp", "tiff", "tif", "gif"}
        return extension.lower() in supported_extensions
    
    def get_supported_extensions(self) -> Set[str]:
        """
        Retorna a lista de extensões suportadas pelo parser.
        
        Returns:
            Conjunto com as extensões suportadas
        """
        return {"jpg", "jpeg", "png", "bmp", "tiff", "tif", "gif"}
    
    def parse(self, file_path: Path) -> Document:
        """
        Converte um arquivo de imagem em um documento.
        
        Args:
            file_path: Caminho para o arquivo de imagem
            
        Returns:
            Documento com o conteúdo e metadados da imagem
        """
        # Verifica se o arquivo existe
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        # Obtém o caminho absoluto
        absolute_path = str(file_path.absolute())
        
        # Tenta extrair texto da imagem
        try:
            # Primeiro, tenta detectar tabelas na imagem
            tables = self.ocr_service.detect_tables(absolute_path)
            
            # Se houver tabelas, extrai os dados delas
            if tables:
                # Prepara o conteúdo combinando dados das tabelas
                content = self._format_table_content(tables)
            else:
                # Se não houver tabelas, faz a extração de texto normal
                ocr_result = self.ocr_service.extract_text(
                    image_path=absolute_path,
                    language="por",
                    preprocess=True
                )
                content = ocr_result["text"]
                
            # Extrai metadados
            metadata = self._extract_metadata(file_path, tables=tables)
            
            # Cria e retorna o documento
            return Document(
                id=file_path.name,
                content=content,
                doc_type=DocumentType.IMAGE,
                metadata=metadata
            )
            
        except Exception as e:
            # Se houver erro na extração, cria um documento com conteúdo vazio
            # mas mantém a referência à imagem
            metadata = self._extract_metadata(file_path, error=str(e))
            
            return Document(
                id=file_path.name,
                content="",
                doc_type=DocumentType.IMAGE,
                metadata=metadata
            )
    
    def _extract_metadata(
        self, 
        file_path: Path, 
        tables: Optional[list] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extrai metadados do arquivo de imagem.
        
        Args:
            file_path: Caminho para o arquivo de imagem
            tables: Informações sobre tabelas detectadas (opcional)
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
            "title": file_path.stem,
            "has_text": False  # Por padrão, assume que não há texto
        }
        
        # Adiciona informações sobre tabelas, se disponíveis
        if tables:
            metadata["has_tables"] = True
            metadata["table_count"] = len(tables)
            metadata["has_text"] = True
            
        # Adiciona informação de erro, se houver
        if error:
            metadata["error"] = error
            
        # Tenta extrair dimensões da imagem
        try:
            import cv2
            image = cv2.imread(str(file_path))
            if image is not None:
                height, width, channels = image.shape
                # Armazena as dimensões como valores primitivos individuais em vez de um dicionário aninhado
                metadata["image_width"] = int(width)
                metadata["image_height"] = int(height)
                metadata["image_channels"] = int(channels)
        except Exception as e:
            # Se não conseguir extrair as dimensões, não adiciona essa informação
            metadata["image_error"] = str(e)
            
        return metadata
    
    def _format_table_content(self, tables: list) -> str:
        """
        Formata o conteúdo das tabelas em texto legível.
        
        Args:
            tables: Lista de tabelas detectadas
            
        Returns:
            Conteúdo formatado
        """
        content = ""
        
        for i, table in enumerate(tables):
            content += f"Tabela {i+1}:\n"
            
            # Se tiver dados extraídos
            if "data" in table:
                table_data = table["data"]
                
                # Formata cada linha da tabela
                for row in table_data:
                    content += " | ".join(row) + "\n"
                    
                content += "\n"
            else:
                content += f"(Tabela detectada nas coordenadas {table['coordinates']})\n\n"
                
        return content 