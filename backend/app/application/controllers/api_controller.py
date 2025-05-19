from fastapi import FastAPI, HTTPException, Depends, Query, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional, Union
import os
import uuid
import tempfile
import shutil
import json
from pathlib import Path
from pydantic import BaseModel, Field
import re

from backend.app.application.services.indexer_service import IndexerService
from backend.app.application.services.prompt_service import PromptServiceImpl
from backend.app.domain.usecases.generate_adaptive_response_usecase import GenerateAdaptiveResponseUseCase
from backend.app.infrastructure.repositories.json_user_progress_repository import JsonUserProgressRepository

# Importa opcionalmente o serviço de rede neural
try:
    from backend.app.application.services.neural_network_service import NeuralNetworkService
except ImportError:
    print("AVISO: PyTorch não está instalado. Recursos de rede neural não estarão disponíveis no controlador.")
    NeuralNetworkService = None


# Modelos Pydantic para validação de dados
class QueryRequest(BaseModel):
    query: str
    user_level: Optional[str] = "intermediário"
    preferred_format: Optional[str] = "texto"
    user_id: Optional[str] = None
    use_neural_network: Optional[bool] = False


class FeedbackRequest(BaseModel):
    user_id: str
    query_id: str
    feedback: str


class IndexRequest(BaseModel):
    directory_path: Optional[str] = None
    file_paths: Optional[List[str]] = None


class RelatedContent(BaseModel):
    id: str
    title: str
    type: str
    content_preview: str
    source: Optional[str] = None


class AnalyzeResponse(BaseModel):
    success: bool = True
    user_id: str
    query_id: Optional[str] = None
    response: str
    related_content: List[RelatedContent] = []
    neural_enhanced: bool = False
    has_video_content: bool = False
    has_audio_content: bool = False
    has_image_content: bool = False
    file_path: Optional[str] = None
    primary_media_type: Optional[str] = None


class SearchResultMetadata(BaseModel):
    source: Optional[str] = None
    title: Optional[str] = None
    size_bytes: Optional[int] = None
    pages: Optional[int] = None
    duration_seconds: Optional[int] = None


class SearchResult(BaseModel):
    id: str
    type: str
    content_preview: str
    metadata: SearchResultMetadata = Field(default_factory=SearchResultMetadata)


class SearchResponse(BaseModel):
    success: bool = True
    query: str
    count: int
    results: List[SearchResult] = []
    neural_enhanced: bool = False


class NeuralNetworkStatusResponse(BaseModel):
    status: str
    available: bool
    user_models: int = 0
    vocab_size: int = 0
    message: str


class ApiController:
    """
    Controlador da API REST que substitui completamente o Express.js.
    """
    
    def __init__(self):
        """
        Inicializa o controlador da API.
        """
        self.app = FastAPI(
            title="A.Educação API",
            description="API para sistema de aprendizagem adaptativa",
            version="1.0.0"
        )
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.user_progress_repository = JsonUserProgressRepository()
        
        self._setup_services()
        
        self._register_endpoints()
        
    def _setup_services(self):
        """
        Configura os serviços necessários.
        """
        base_dir = Path(os.path.dirname(__file__)).parent.parent.parent
        chroma_dir = os.path.join(base_dir, "database", "chromadb")
        os.makedirs(chroma_dir, exist_ok=True)
        
        upload_dir = os.path.join(base_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        self.upload_dir = upload_dir
        
        models_dir = os.path.join(base_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        
        import chromadb
        chroma_client = chromadb.PersistentClient(path=chroma_dir)
        self.indexer_service = IndexerService(
            chroma_client=chroma_client,
            collection_name="a_educacao",
            user_progress_repository=self.user_progress_repository
        )
        
        self.neural_network_service = None
        if NeuralNetworkService:
            try:
                self.neural_network_service = NeuralNetworkService(
                    user_progress_repository=self.user_progress_repository,
                    model_dir=models_dir
                )
                print("Serviço de rede neural inicializado no controlador API.")
            except Exception as e:
                print(f"Erro ao inicializar serviço de rede neural no controlador: {e}")
        
        self.prompt_service = PromptServiceImpl(
            search_service=self.indexer_service.search_service,
            user_progress_repository=self.user_progress_repository
        )
        
        self.adaptive_response_usecase = GenerateAdaptiveResponseUseCase(
            prompt_service=self.prompt_service,
            neural_service=self.neural_network_service
        )
        
        try:
            from backend.app.infrastructure.services.directory_watcher_service import DirectoryWatcherService
            
            resources_dir = os.path.join(base_dir, "resources")
            watch_directories = [resources_dir, upload_dir]
            
            os.makedirs(resources_dir, exist_ok=True)
            
            self.directory_watcher = DirectoryWatcherService(
                indexer_service=self.indexer_service,
                directories_to_watch=watch_directories
            )
            
            self.directory_watcher.start()
            
        except ImportError:
            print("AVISO: Watchdog não está instalado. O monitoramento automático de diretórios não estará disponível.")
            print("Instale com: pip install watchdog")
        except Exception as e:
            print(f"Erro ao iniciar monitoramento de diretórios: {e}")
        
    def _register_endpoints(self):
        """
        Registra os endpoints da API.
        """
        app = self.app
        
        # Configura CORS para permitir requisições de qualquer origem
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Define o diretório base do projeto
        base_dir = Path(os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", "..", ".."
        )))
        
        # Diretório de recursos processados
        processed_data_dir = base_dir / "processed_data"
        
        # Configura o endpoint para servir arquivos estáticos da pasta processed_data
        from fastapi.staticfiles import StaticFiles
        app.mount("/processed_data", StaticFiles(directory=str(processed_data_dir)), name="processed_data")
        
        # Endpoint para verificar o status da API
        @app.get("/")
        def read_root():
            return {
                "status": "ok", 
                "message": "A.Educação API está funcionando"
            }
        
        # Endpoint para indexar conteúdo
        @app.post("/api/index")
        async def index_content(request: IndexRequest):
            success = False
            indexed_files = []
            errors = []
            
            try:
                # Se um diretório for especificado, indexa todos os arquivos nele
                if request.directory_path:
                    if not os.path.exists(request.directory_path):
                        raise HTTPException(status_code=400, detail=f"Diretório não encontrado: {request.directory_path}")
                        
                    success = self.indexer_service.index_data(request.directory_path)
                    if success:
                        indexed_files = [
                            str(f.relative_to(request.directory_path)) 
                            for f in Path(request.directory_path).glob("**/*") 
                            if f.is_file()
                        ]
                
                # Se arquivos específicos forem especificados, indexa cada um
                elif request.file_paths:
                    # Itera sobre cada arquivo
                    for file_path in request.file_paths:
                        if not os.path.exists(file_path):
                            errors.append(f"Arquivo não encontrado: {file_path}")
                            continue
                            
                        # Determina o tipo de arquivo e usa o método apropriado
                        extension = os.path.splitext(file_path)[1].lower()
                        file_indexed = False
                        
                        if extension in ['.txt', '.md', '.csv']:
                            file_indexed = self.indexer_service.index_text(file_path)
                        elif extension in ['.pdf']:
                            file_indexed = self.indexer_service.index_pdf(file_path)
                        elif extension in ['.mp4', '.avi', '.mov', '.mkv']:
                            file_indexed = self.indexer_service.index_video(file_path)
                        elif extension in ['.jpg', '.jpeg', '.png', '.gif']:
                            file_indexed = self.indexer_service.index_image(file_path)
                        elif extension in ['.json']:
                            file_indexed = self.indexer_service.index_text(file_path)
                        else:
                            errors.append(f"Tipo de arquivo não suportado: {file_path}")
                            continue
                            
                        if file_indexed:
                            indexed_files.append(file_path)
                            success = True
                        else:
                            errors.append(f"Falha ao indexar: {file_path}")
                else:
                    raise HTTPException(status_code=400, detail="É necessário especificar directory_path ou file_paths")
                
                # Retorna os resultados
                return {
                    "success": success,
                    "indexed_files": indexed_files,
                    "errors": errors,
                    "total_indexed": len(indexed_files)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao indexar conteúdo: {str(e)}")
                
        # Endpoint para fazer upload e indexar arquivos
        @app.post("/api/upload")
        async def upload_files(
            background_tasks: BackgroundTasks,
            files: List[UploadFile] = File(...)
        ):
            uploaded_files = []
            errors = []
            
            try:
                # Verifica se algum arquivo foi enviado
                if not files:
                    raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
                
                # Processa cada arquivo
                for file in files:
                    timestamp = str(uuid.uuid4())
                    file_path = os.path.join(self.upload_dir, f"{timestamp}-{file.filename}")
                    
                    # Salva o arquivo
                    with open(file_path, "wb") as buffer:
                        content = await file.read()
                        buffer.write(content)
                        
                    uploaded_files.append({
                        "filename": file.filename,
                        "path": file_path
                    })
                
                # Indexa os arquivos em segundo plano
                def index_uploaded_files():
                    for file_info in uploaded_files:
                        file_path = file_info["path"]
                        filename = file_info["filename"]
                        extension = os.path.splitext(file_path)[1].lower()
                        
                        try:
                            if extension in ['.txt', '.md', '.csv']:
                                self.indexer_service.index_text(file_path)
                            elif extension in ['.pdf']:
                                self.indexer_service.index_pdf(file_path)
                            elif extension in ['.mp4', '.avi', '.mov', '.mkv']:
                                self.indexer_service.index_video(file_path)
                            elif extension in ['.jpg', '.jpeg', '.png', '.gif']:
                                self.indexer_service.index_image(file_path)
                            elif extension in ['.json']:
                                self.indexer_service.index_text(file_path)
                            else:
                                errors.append(f"Tipo de arquivo não suportado: {filename}")
                        except Exception as e:
                            errors.append(f"Erro ao indexar {filename}: {str(e)}")
                
                # Agenda a tarefa de indexação em segundo plano
                background_tasks.add_task(index_uploaded_files)
                
                return {
                    "success": True,
                    "message": "Arquivos enviados com sucesso. A indexação está em andamento.",
                    "uploaded_files": [file["filename"] for file in uploaded_files]
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao processar upload: {str(e)}")
                
        # Endpoint para buscar conteúdo
        @app.get("/api/search", response_model=SearchResponse)
        def search_content(
            q: str = Query(..., description="Termo de busca"),
            limit: int = Query(5, description="Número máximo de resultados"),
            doc_type: Optional[str] = Query(None, description="Tipo de documento (text, pdf, video, image, json)"),
            user_id: Optional[str] = Query(None, description="ID do usuário para personalização"),
            use_neural: bool = Query(False, description="Usar rede neural para ordenar resultados")
        ):
            try:
                if not q:
                    raise HTTPException(status_code=400, detail="É necessário especificar o parâmetro de busca (q)")
                
                # Flag para indicar se a busca foi aprimorada pela rede neural
                neural_enhanced = False
                
                # Realiza a busca
                if use_neural and user_id and self.neural_network_service:
                    try:
                        # Tenta usar ordenação neural
                        if doc_type:
                            # Busca por tipo com resultados extras para permitir ordenação
                            docs = self.indexer_service.search_by_type(q, doc_type, limit * 2)
                            # Ordena usando a rede neural
                            if docs:
                                ranked_docs = self.neural_network_service.predict_relevance(user_id, docs)
                                docs = [doc for doc, _ in ranked_docs[:limit]]
                                neural_enhanced = True
                        else:
                            # Busca com ordenação neural
                            docs = self.indexer_service.search_with_neural_ranking(q, user_id, limit)
                            neural_enhanced = True if docs else False
                    except Exception as e:
                        print(f"Erro ao usar ordenação neural na busca: {e}")
                        # Em caso de erro, recorre à busca normal
                        if doc_type:
                            docs = self.indexer_service.search_by_type(q, doc_type, limit)
                        else:
                            docs = self.indexer_service.search(q, limit)
                else:
                    # Realiza busca normal
                    if doc_type:
                        docs = self.indexer_service.search_by_type(q, doc_type, limit)
                    else:
                        docs = self.indexer_service.search(q, limit)
                    
                # Formata os resultados
                results = []
                for doc in docs:
                    # Limita a prévia do conteúdo a 300 caracteres
                    content_preview = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                    
                    # Extrai metadados relevantes
                    metadata = {}
                    if doc.metadata:
                        for key in ["source", "title", "size_bytes", "pages", "duration_seconds"]:
                            if key in doc.metadata:
                                metadata[key] = doc.metadata[key]
                    
                    # Cria o objeto de resultado
                    result = SearchResult(
                        id=doc.id,
                        type=doc.doc_type.value,
                        content_preview=content_preview,
                        metadata=SearchResultMetadata(**metadata)
                    )
                    results.append(result)
                    
                # Retorna a resposta formatada
                return SearchResponse(
                    success=True,
                    query=q,
                    count=len(results),
                    results=results,
                    neural_enhanced=neural_enhanced
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")
                
        # Endpoint para analisar consultas e gerar respostas adaptativas
        @app.post("/api/analyze", response_model=AnalyzeResponse)
        def analyze_query(request: QueryRequest):
            """
            Analisa uma consulta e retorna uma resposta adaptativa.
            """
            try:
                # Gera um ID para o usuário se não fornecido
                user_id = request.user_id or str(uuid.uuid4())
                
                # Gera um ID para a consulta
                query_id = str(uuid.uuid4())
                
                # Determina se deve usar a rede neural
                use_neural = request.use_neural_network and self.neural_network_service is not None
                
                # Busca resultados relacionados à consulta
                search_results = self.indexer_service.search_service.search(
                    query=request.query,
                    limit=5
                )
                
                # Prepara o conteúdo relacionado
                related_content = []
                for result in search_results:
                    # Extrai informações do resultado
                    doc_id = result.get("id", "") if hasattr(result, "get") else getattr(result, "id", "")
                    doc_content = result.get("content", "") if hasattr(result, "get") else getattr(result, "content", "")
                    doc_metadata = result.get("metadata", {}) if hasattr(result, "get") else getattr(result, "metadata", {})
                    
                    # Se doc_metadata não for um dicionário, trata como um objeto
                    if not isinstance(doc_metadata, dict) and hasattr(doc_metadata, "__dict__"):
                        doc_metadata = doc_metadata.__dict__
                    elif not isinstance(doc_metadata, dict):
                        doc_metadata = {}
                        
                    doc_source = doc_metadata.get("source", "") if isinstance(doc_metadata, dict) else getattr(doc_metadata, "source", "")
                    doc_title = doc_metadata.get("title", doc_id) if isinstance(doc_metadata, dict) else getattr(doc_metadata, "title", doc_id)
                    
                    # Determina o tipo de documento
                    doc_type = "text"
                    if doc_source:
                        if doc_source.endswith((".jpg", ".jpeg", ".png", ".gif")):
                            doc_type = "image"
                        elif doc_source.endswith((".mp4", ".avi", ".mov")):
                            doc_type = "video"
                        elif doc_source.endswith((".mp3", ".wav", ".ogg")):
                            doc_type = "audio"
                        elif doc_source.endswith((".pdf")):
                            doc_type = "pdf"
                    
                    # Adiciona à lista de conteúdo relacionado
                    related_content.append(RelatedContent(
                        id=doc_id,
                        title=doc_title or doc_id,
                        type=doc_type,
                        content_preview=doc_content[:150] + "..." if len(doc_content) > 150 else doc_content,
                        source=doc_source
                    ))
                
                # Gera a resposta adaptativa
                response = self.adaptive_response_usecase.generate_response(
                    query=request.query,
                    user_id=user_id,
                    user_level=request.user_level,
                    preferred_format=request.preferred_format
                )
                
                # Extrai o caminho do arquivo da resposta, se houver
                file_path = None
                primary_media_type = "mixed"  # Definimos como mixed por padrão
                has_video = False
                has_audio = False
                has_image = False
                
                # Verifica se há menção a arquivos de mídia na resposta
                if "vídeo" in response.lower() or "video" in response.lower():
                    has_video = True
                    file_path = file_path or "videos/Dica do professor.mp4"
                
                if "áudio" in response.lower() or "audio" in response.lower():
                    has_audio = True
                    file_path = file_path or "audio/Dica do professor.mp3"
                
                if "imagem" in response.lower() or "image" in response.lower():
                    has_image = True
                    file_path = file_path or "images/Infografico-1.jpg"
                
                # Procura por caminhos de arquivo na resposta
                file_match = re.search(r'<!-- file_path: (.*?) -->', response)
                if file_match:
                    file_path = file_match.group(1)
                    
                    # Determina o tipo de mídia com base na extensão
                    if file_path.endswith((".mp4", ".avi", ".mov", ".webm")):
                        primary_media_type = "video"
                        has_video = True
                    elif file_path.endswith((".mp3", ".wav", ".ogg", ".aac")):
                        primary_media_type = "audio"
                        has_audio = True
                    elif file_path.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        primary_media_type = "image"
                        has_image = True
                    elif "exercicio" in file_path.lower() or "exercício" in file_path.lower():
                        primary_media_type = "exercises"
                    else:
                        primary_media_type = "text"
                
                # Retorna a resposta formatada
                return AnalyzeResponse(
                    success=True,
                    user_id=user_id,
                    query_id=query_id,
                    response=response,
                    related_content=related_content,
                    neural_enhanced=use_neural,
                    has_video_content=has_video,
                    has_audio_content=has_audio,
                    has_image_content=has_image,
                    file_path=file_path,
                    primary_media_type=primary_media_type
                )
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Erro ao processar consulta: {str(e)}")
                
        # Endpoint para receber feedback
        @app.post("/api/feedback")
        def receive_feedback(request: FeedbackRequest):
            try:
                if not request.user_id or not request.query_id or not request.feedback:
                    raise HTTPException(
                        status_code=400, 
                        detail="Campos obrigatórios: user_id, query_id e feedback"
                    )
                    
                # Salva o feedback no repositório
                success = self.user_progress_repository.update_interaction(
                    user_id=request.user_id,
                    query="",  # Não temos a consulta original, apenas o ID dela
                    response="",  # Não temos a resposta original, apenas o feedback
                    feedback=request.feedback
                )
                
                # Se o serviço neural estiver disponível, treina o modelo com o feedback
                neural_updated = False
                if self.neural_network_service:
                    try:
                        # Treina o modelo com base nos feedbacks acumulados
                        loss = self.neural_network_service.train_from_feedback(request.user_id)
                        neural_updated = True
                    except Exception as e:
                        print(f"Erro ao treinar modelo neural com feedback: {e}")
                
                # Retorna sucesso
                return {
                    "success": success,
                    "neural_updated": neural_updated
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao processar feedback: {str(e)}")
                
        # Endpoint para verificar o status da rede neural
        @app.get("/api/neural-status")
        def neural_network_status():
            """
            Verifica o status da rede neural.
            """
            if not self.neural_network_service:
                return NeuralNetworkStatusResponse(
                    status="unavailable",
                    available=False,
                    message="Serviço de rede neural não está disponível. Verifique se PyTorch está instalado."
                )
                
            try:
                # Coleta informações sobre o serviço neural
                user_models = len(self.neural_network_service.models)
                vocab_size = self.neural_network_service.vocab_size
                
                return NeuralNetworkStatusResponse(
                    status="active",
                    available=True,
                    user_models=user_models,
                    vocab_size=vocab_size,
                    message="Serviço de rede neural está ativo e funcionando corretamente."
                )
                
            except Exception as e:
                return NeuralNetworkStatusResponse(
                    status="error",
                    available=True,
                    message=f"Erro ao verificar status da rede neural: {str(e)}"
                )
                
        # Endpoint para obter recomendações proativas
        @app.get("/api/recommendations/{user_id}")
        def get_recommendations(user_id: str):
            """
            Obtém recomendações personalizadas para um usuário.
            """
            try:
                if not user_id:
                    raise HTTPException(status_code=400, detail="ID de usuário é obrigatório")
                    
                # Obtém o progresso do usuário
                user_progress = self.user_progress_repository.get_by_id(user_id)
                
                if not user_progress:
                    # Se não existe progresso, retorna recomendações genéricas
                    generic_recommendations = self.prompt_service.suggest_related_content(
                        query="aprendizagem adaptativa",
                        limit=3
                    )
                    
                    return {
                        "success": True,
                        "user_id": user_id,
                        "is_personalized": False,
                        "recommendations": [
                            {
                                "id": item.get("id", str(uuid.uuid4())),
                                "title": item.get("title", "Conteúdo recomendado"),
                                "type": item.get("type", "text"),
                                "content_preview": item.get("preview", ""),
                                "source": item.get("source")
                            }
                            for item in generic_recommendations
                        ]
                    }
                
                # Obtém recomendações baseadas nas interações do usuário
                recommendations = []
                
                # Obtém as consultas recentes do usuário
                recent_interactions = user_progress.get_recent_interactions(5)
                
                if recent_interactions:
                    # Combina consultas recentes para gerar recomendações relevantes
                    combined_query = " ".join([interaction.query for interaction in recent_interactions[:3]])
                    
                    # Busca conteúdos relacionados às consultas recentes
                    recommendations = self.prompt_service.suggest_related_content(
                        query=combined_query,
                        user_level=user_progress.profile.level,
                        limit=5
                    )
                else:
                    # Se não há interações recentes, usa o perfil do usuário
                    if user_progress.profile.interests:
                        interests_query = " ".join(user_progress.profile.interests[:3])
                        recommendations = self.prompt_service.suggest_related_content(
                            query=interests_query,
                            user_level=user_progress.profile.level,
                            limit=5
                        )
                    else:
                        # Se não há interesses definidos, usa recomendações genéricas
                        recommendations = self.prompt_service.suggest_related_content(
                            query="aprendizagem adaptativa",
                            user_level=user_progress.profile.level,
                            limit=3
                        )
                
                # Formata as recomendações
                formatted_recommendations = [
                    {
                        "id": item.get("id", str(uuid.uuid4())),
                        "title": item.get("title", "Conteúdo recomendado"),
                        "type": item.get("type", "text"),
                        "content_preview": item.get("preview", ""),
                        "source": item.get("source")
                    }
                    for item in recommendations
                ]
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "is_personalized": True,
                    "recommendations": formatted_recommendations,
                    "user_level": user_progress.profile.level,
                    "preferred_format": user_progress.profile.preferred_format
                }
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao obter recomendações: {str(e)}")
                
    def get_app(self) -> FastAPI:
        """
        Retorna a instância do aplicativo FastAPI.
        
        Returns:
            FastAPI: A instância do aplicativo.
        """
        return self.app 