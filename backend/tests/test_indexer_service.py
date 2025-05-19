import unittest
import os
import tempfile
from pathlib import Path
import chromadb

from services.indexer_service import IndexerService


class TestIndexerService(unittest.TestCase):
    """
    Testes para o serviço de indexação.
    """
    
    def setUp(self):
        """
        Configuração dos testes.
        """
        # Criar um diretório temporário para os testes
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Inicializar o cliente ChromaDB em memória para testes
        self.chroma_client = chromadb.Client()
        
        # Inicializar o serviço de indexação
        self.indexer = IndexerService(
            chroma_client=self.chroma_client,
            collection_name="test_collection"
        )
        
        # Criar alguns arquivos de teste
        self.create_test_files()
        
    def tearDown(self):
        """
        Limpeza após os testes.
        """
        # Remover o diretório temporário
        self.temp_dir.cleanup()
        
    def create_test_files(self):
        """
        Cria arquivos de teste no diretório temporário.
        """
        # Arquivo de texto
        self.text_file = Path(self.temp_dir.name) / "test.txt"
        with open(self.text_file, "w", encoding="utf-8") as f:
            f.write("Este é um arquivo de texto para teste do indexador.")
            
        # Arquivo JSON (simples para teste)
        self.json_file = Path(self.temp_dir.name) / "test.json"
        with open(self.json_file, "w", encoding="utf-8") as f:
            f.write('{"title": "Teste", "content": "Este é um conteúdo de teste em JSON."}')
            
    def test_index_text(self):
        """
        Testa a indexação de um arquivo de texto.
        """
        # Executar a indexação
        result = self.indexer.index_text(str(self.text_file))
        
        # Verificar se a indexação foi bem-sucedida
        self.assertTrue(result)
        
        # Verificar se o documento está no repositório
        document = self.indexer.repository.get_by_id(self.text_file.name)
        self.assertIsNotNone(document)
        self.assertEqual(document.id, self.text_file.name)
        
    def test_index_json(self):
        """
        Testa a indexação de um arquivo JSON.
        """
        # Executar a indexação
        result = self.indexer.index_data(self.temp_dir.name)
        
        # Verificar se a indexação foi bem-sucedida
        self.assertTrue(result)
        
        # Verificar se o documento JSON está no repositório
        document = self.indexer.repository.get_by_id(self.json_file.name)
        self.assertIsNotNone(document)
        self.assertEqual(document.id, self.json_file.name)
        
    def test_index_directory(self):
        """
        Testa a indexação de um diretório.
        """
        # Executar a indexação
        result = self.indexer.index_data(self.temp_dir.name)
        
        # Verificar se a indexação foi bem-sucedida
        self.assertTrue(result)
        
        # Buscar um termo que deve estar nos documentos
        documents = self.indexer.repository.search("teste")
        
        # Deve encontrar pelo menos um documento
        self.assertGreater(len(documents), 0)


if __name__ == "__main__":
    unittest.main() 