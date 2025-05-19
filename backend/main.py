import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import chromadb

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa o controller da API
from backend.app.application.controllers.api_controller import ApiController
from backend.app.application.controllers.enhanced_api_controller import EnhancedApiController
from backend.app.application.controllers.admin_controller import router as admin_router
from backend.app.application.controllers.learning_gaps_controller import LearningGapsController
from backend.app.infrastructure.repositories.json_user_progress_repository import JsonUserProgressRepository
from backend.app.application.services.enhanced_search_service import EnhancedSearchService
from backend.app.application.services.enhanced_prompt_service import EnhancedPromptServiceImpl
from backend.app.application.services.indexer_service import IndexerService
from backend.app.infrastructure.repositories.chroma_document_repository import ChromaDocumentRepository

# Versão do sistema
VERSION = "1.0.0"

def create_app() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI.
    
    Returns:
        FastAPI: Aplicação configurada
    """
    app = FastAPI(
        title="A.Educação API",
        description="API para sistema de aprendizagem adaptativa",
        version="1.0.0"
    )
    
    # Configuração de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permitir todas as origens em desenvolvimento
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configurações básicas para diretórios de trabalho
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    resources_dir = base_dir / "resources"
    
    # Diretórios para dados processados
    processed_data_dir = base_dir / "processed_data"
    text_dir = processed_data_dir / "text"
    audio_dir = processed_data_dir / "audio"
    transcripts_dir = processed_data_dir / "transcripts"
    videos_dir = processed_data_dir / "videos"
    images_dir = processed_data_dir / "images"
    
    # Configurar rotas para servir arquivos estáticos
    app.mount("/processed_data", StaticFiles(directory=str(processed_data_dir)), name="processed_data")
    
    # Diretório para o ChromaDB
    chroma_dir = base_dir / "database" / "chromadb"
    os.makedirs(chroma_dir, exist_ok=True)
    
    # Inicializar o cliente ChromaDB
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    
    # Inicializar o repositório de usuários
    user_repository = JsonUserProgressRepository()
    
    # Inicializar o repositório de documentos
    document_repository = ChromaDocumentRepository(
        chroma_client=chroma_client,
        collection_name="a_educacao"
    )
    
    # Inicializar serviços
    indexer_service = IndexerService(
        chroma_client=chroma_client,
        collection_name="a_educacao",
        user_progress_repository=user_repository
    )
    
    # Inicializar controladores API
    api_controller = ApiController()
    app.include_router(api_controller.get_app().router)
    
    # Inicializar serviços aprimorados
    search_service = EnhancedSearchService(document_repository=document_repository)
    prompt_service = EnhancedPromptServiceImpl(
        search_service=search_service,
        user_progress_repository=user_repository
    )
    
    # Inicializar controlador API aprimorado
    enhanced_api = EnhancedApiController(
        app=app, 
        indexer_service=indexer_service,
        search_service=search_service,
        prompt_service=prompt_service
    )
    
    # Inicializar controlador de lacunas de aprendizado
    learning_gaps_controller = LearningGapsController(
        user_repository=user_repository,
        search_service=search_service
    )
    app.include_router(learning_gaps_controller.get_router())
    
    # Incluir router do controlador administrativo
    app.include_router(admin_router)
    
    # Indexar arquivos processados existentes ao iniciar
    @app.on_event("startup")
    async def startup_event():
        print("Iniciando indexação de arquivos processados...")
        
        # Indexar arquivos de texto
        if os.path.exists(text_dir):
            for file_path in text_dir.glob("*.txt"):
                try:
                    indexer_service.index_text(str(file_path))
                    print(f"Indexado: {file_path}")
                except Exception as e:
                    print(f"Erro ao indexar {file_path}: {e}")
        
        # Indexar transcrições
        if os.path.exists(transcripts_dir):
            for file_path in transcripts_dir.glob("*_ocr.txt"):
                try:
                    indexer_service.index_text(str(file_path))
                    print(f"Indexado: {file_path}")
                except Exception as e:
                    print(f"Erro ao indexar {file_path}: {e}")
                    
        # Indexar arquivos PDF (já convertidos para texto)
        for file_path in text_dir.glob("*.pdf.txt"):
            try:
                indexer_service.index_text(str(file_path))
                print(f"Indexado PDF: {file_path}")
            except Exception as e:
                print(f"Erro ao indexar PDF {file_path}: {e}")
        
        print("Indexação concluída!")
    
    # Endpoint de verificação de saúde
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "message": "API está funcionando corretamente"}
    
    return app

app = create_app()

if __name__ == "__main__":
    # Inicia o servidor com Uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 