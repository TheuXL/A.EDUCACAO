import json
from pathlib import Path
from typing import Optional, Dict, Any

from ...domain.entities.document import Document, DocumentType
from ...domain.interfaces.document_parser import DocumentParser


class JsonParser(DocumentParser):
    """
    Parser para arquivos JSON.
    """
    
    def _flatten_json(self, json_obj: Dict[str, Any], prefix: str = "") -> str:
        """
        Converte um objeto JSON em texto plano.
        
        Args:
            json_obj: Objeto JSON a ser convertido
            prefix: Prefixo para as chaves (usado na recursão)
            
        Returns:
            String com o conteúdo do JSON em formato de texto
        """
        text = []
        
        for key, value in json_obj.items():
            current_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                text.append(self._flatten_json(value, current_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        text.append(self._flatten_json(item, f"{current_key}[{i}]"))
                    else:
                        text.append(f"{current_key}[{i}]: {item}")
            else:
                text.append(f"{current_key}: {value}")
                
        return " ".join(text)
    
    def parse(self, file_path: Path) -> Optional[Document]:
        """
        Processa um arquivo JSON.
        
        Args:
            file_path: Caminho para o arquivo JSON
        
        Returns:
            Document com o conteúdo processado ou None se o processamento falhar
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            # Converter o JSON em texto plano
            text = self._flatten_json(json_data)
            
            return Document(
                id=file_path.name,
                content=text,
                doc_type=DocumentType.JSON,
                metadata={
                    "source": str(file_path),
                    "size_bytes": file_path.stat().st_size
                }
            )
        except Exception as e:
            print(f"Erro ao processar arquivo JSON {file_path}: {e}")
            return None
            
    def supports_extension(self, extension: str) -> bool:
        """
        Verifica se este parser suporta a extensão do arquivo.
        
        Args:
            extension: Extensão do arquivo (sem o ponto)
        
        Returns:
            True se o parser suporta esta extensão, False caso contrário
        """
        return extension.lower() in ["json"] 