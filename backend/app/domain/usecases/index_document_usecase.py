from typing import List, Optional
from pathlib import Path

from ..entities.document import Document
from ..interfaces.document_repository import DocumentRepository
from ..interfaces.document_parser import DocumentParser


class IndexDocumentUseCase:
    """
    Caso de uso para indexação de documentos.
    Coordena o processamento e armazenamento de documentos.
    """
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        parsers: List[DocumentParser]
    ):
        """
        Inicializa o caso de uso de indexação.
        
        Args:
            document_repository: Repositório para armazenar documentos
            parsers: Lista de parsers disponíveis para processar documentos
        """
        self.repository = document_repository
        self.parsers = parsers
        
    def get_parser_for_file(self, file_path: Path) -> Optional[DocumentParser]:
        """
        Encontra o parser adequado para o tipo de arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Parser compatível ou None se nenhum parser suportar o tipo de arquivo
        """
        extension = file_path.suffix.lstrip('.')
        for parser in self.parsers:
            if parser.supports_extension(extension):
                return parser
        return None
        
    def index_file(self, file_path: Path) -> bool:
        """
        Indexa um único arquivo.
        
        Args:
            file_path: Caminho do arquivo a ser indexado
            
        Returns:
            True se indexado com sucesso, False caso contrário
        """
        if not file_path.exists():
            print(f"Arquivo não encontrado: {file_path}")
            return False
            
        parser = self.get_parser_for_file(file_path)
        if not parser:
            print(f"Nenhum parser disponível para o arquivo: {file_path}")
            return False
            
        try:
            document = parser.parse(file_path)
            if document:
                return self.repository.add(document)
            return False
        except Exception as e:
            print(f"Erro ao indexar arquivo {file_path}: {e}")
            return False
            
    def index_directory(self, directory_path: Path) -> bool:
        """
        Indexa todos os arquivos suportados em um diretório.
        
        Args:
            directory_path: Caminho do diretório com arquivos a serem indexados
            
        Returns:
            True se pelo menos um arquivo foi indexado com sucesso, False caso contrário
        """
        if not directory_path.exists() or not directory_path.is_dir():
            print(f"Diretório não encontrado: {directory_path}")
            return False
            
        indexed_count = 0
        total_files = 0
            
        for file_path in directory_path.iterdir():
            if file_path.is_file():
                total_files += 1
                if self.index_file(file_path):
                    indexed_count += 1
                    
        print(f"Indexação concluída: {indexed_count}/{total_files} arquivos indexados")
        return indexed_count > 0 