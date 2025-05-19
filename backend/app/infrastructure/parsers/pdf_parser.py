import re
from pathlib import Path
from typing import Optional
from pypdf import PdfReader

from ...domain.entities.document import Document, DocumentType
from ...domain.interfaces.document_parser import DocumentParser


class PdfParser(DocumentParser):
    """
    Parser para arquivos PDF.
    """
    
    def parse(self, file_path: Path) -> Optional[Document]:
        """
        Processa um arquivo PDF.
        
        Args:
            file_path: Caminho para o arquivo PDF
        
        Returns:
            Document com o conteúdo processado ou None se o processamento falhar
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            
            # Extrair texto de todas as páginas
            for page in reader.pages:
                text += page.extract_text() + " "
                
            # Limpeza básica do texto (remover espaços extras e quebras de linha)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Metadados básicos do PDF
            metadata = {
                "source": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "pages": len(reader.pages)
            }
            
            # Adicionar metadados do PDF se disponíveis
            if reader.metadata:
                pdf_info = reader.metadata
                if pdf_info.title:
                    metadata["title"] = pdf_info.title
                if pdf_info.author:
                    metadata["author"] = pdf_info.author
                if pdf_info.subject:
                    metadata["subject"] = pdf_info.subject
                if pdf_info.creator:
                    metadata["creator"] = pdf_info.creator
            
            return Document(
                id=file_path.name,
                content=text,
                doc_type=DocumentType.PDF,
                metadata=metadata
            )
        except Exception as e:
            print(f"Erro ao processar arquivo PDF {file_path}: {e}")
            return None
            
    def supports_extension(self, extension: str) -> bool:
        """
        Verifica se este parser suporta a extensão do arquivo.
        
        Args:
            extension: Extensão do arquivo (sem o ponto)
        
        Returns:
            True se o parser suporta esta extensão, False caso contrário
        """
        return extension.lower() in ["pdf"] 