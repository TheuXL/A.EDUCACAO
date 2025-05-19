import re
from pathlib import Path
from typing import Optional

from ...domain.entities.document import Document, DocumentType
from ...domain.interfaces.document_parser import DocumentParser


class TextParser(DocumentParser):
    """
    Parser para arquivos de texto.
    """
    
    def parse(self, file_path: Path) -> Optional[Document]:
        """
        Processa um arquivo de texto.
        
        Args:
            file_path: Caminho para o arquivo de texto
        
        Returns:
            Document com o conteúdo processado ou None se o processamento falhar
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # Limpeza básica do texto (remover espaços extras e quebras de linha)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return Document(
                id=file_path.name,
                content=text,
                doc_type=DocumentType.TEXT,
                metadata={
                    "source": str(file_path),
                    "size_bytes": file_path.stat().st_size
                }
            )
        except Exception as e:
            print(f"Erro ao processar arquivo de texto {file_path}: {e}")
            return None
            
    def supports_extension(self, extension: str) -> bool:
        """
        Verifica se este parser suporta a extensão do arquivo.
        
        Args:
            extension: Extensão do arquivo (sem o ponto)
        
        Returns:
            True se o parser suporta esta extensão, False caso contrário
        """
        return extension.lower() in ["txt"] 