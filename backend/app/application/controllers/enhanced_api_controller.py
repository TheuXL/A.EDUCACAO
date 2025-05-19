import os
import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, BackgroundTasks

from backend.app.application.services.enhanced_search_service import EnhancedSearchService
from backend.app.application.services.enhanced_prompt_service import EnhancedPromptServiceImpl
from backend.app.application.services.indexer_service import IndexerService

class EnhancedApiController:
    """
    Controlador API aprimorado para o sistema A.Educação.
    
    Características:
    - Suporte para busca e respostas adaptativas melhoradas
    - Melhor tratamento de conteúdo baseado em formato (texto, vídeo, imagem)
    - Indicação de confiança nas respostas
    """
    
    def __init__(
        self, 
        app: FastAPI, 
        indexer_service: IndexerService,
        search_service: EnhancedSearchService,
        prompt_service: EnhancedPromptServiceImpl
    ):
        """
        Inicializa o controlador API.
        
        Args:
            app: Aplicação FastAPI
            indexer_service: Serviço de indexação
            search_service: Serviço de busca
            prompt_service: Serviço de prompt para geração de respostas
        """
        self.app = app
        self.indexer_service = indexer_service
        self.search_service = search_service
        self.prompt_service = prompt_service
        
        self.upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        
        self.conversation_history = {}
        
        self._register_endpoints()
        
    def _register_endpoints(self):
        """
        Registra os endpoints da API.
        """
        @self.app.get("/api/search")
        async def search(
            query: str = Query(..., description="Consulta a ser pesquisada"), 
            limit: int = Query(5, description="Número máximo de resultados"),
            format: str = Query(None, description="Filtrar por formato específico (texto, video, imagem)")
        ):
            """
            Endpoint para pesquisa de conteúdo.
            """
            try:
                if format:
                    format_to_doctype = {
                        "texto": "text",
                        "vídeo": "video",
                        "video": "video",
                        "imagem": "image"
                    }
                    doc_type = format_to_doctype.get(format.lower())
                    
                    if doc_type:
                        results = self.search_service.search_by_type(query, doc_type, limit)
                    else:
                        results = self.search_service.search(query, limit)
                else:
                    results = self.search_service.search(query, limit)
                
                search_results = []
                for doc in results:
                    search_results.append({
                        "id": doc.id,
                        "type": doc.doc_type.value,
                        "preview": doc.content[:150] + "..." if len(doc.content) > 150 else doc.content,
                        "source": doc.metadata.get("source", "") if doc.metadata else "",
                        "title": doc.metadata.get("title", "Untitled") if doc.metadata else "Untitled"
                    })
                
                return {"query": query, "results": search_results}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao realizar busca: {str(e)}")
        
        @self.app.post("/api/analyze")
        async def analyze(
            query: str = Form(..., description="Consulta do usuário"),
            user_level: str = Form("intermediário", description="Nível de conhecimento do usuário"),
            preferred_format: str = Form("texto", description="Formato preferido (texto, vídeo, imagem)"),
            user_id: Optional[str] = Form(None, description="ID do usuário (opcional)"),
            conversation_id: Optional[str] = Form(None, description="ID da conversa (opcional)"),
            use_neural_network: bool = Form(False, description="Usar rede neural para melhorar respostas")
        ):
            """
            Endpoint para análise e resposta adaptativa.
            Suporta contexto conversacional e adaptação ao perfil do usuário.
            """
            try:
                valid_levels = ["iniciante", "intermediário", "avançado"]
                if user_level not in valid_levels:
                    user_level = "intermediário"
                
                valid_formats = ["texto", "vídeo", "imagem", "áudio"]
                if preferred_format not in valid_formats:
                    preferred_format = "texto"
                
                if not user_id:
                    user_id = str(uuid.uuid4())
                
                if not conversation_id:
                    conversation_id = str(uuid.uuid4())
                else:
                    if conversation_id not in self.conversation_history:
                        self.conversation_history[conversation_id] = []
                
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                
                conversation_history = self.conversation_history[conversation_id]
                
                response = self.prompt_service.generate_response(
                    query=query,
                    user_level=user_level,
                    preferred_format=preferred_format,
                    user_id=user_id,
                    conversation_history=conversation_history
                )
                
                self.conversation_history[conversation_id] = conversation_history[-10:]
                
                related_content = self.prompt_service.suggest_related_content(
                    query=query,
                    user_level=user_level,
                    limit=3
                )
                
                has_video = "📺" in response and preferred_format == "vídeo"
                has_image = "🖼️" in response and preferred_format == "imagem"
                has_audio = "🔊" in response and preferred_format == "áudio"
                
                response_data = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "query": query, 
                    "response": response,
                    "user_level": user_level,
                    "preferred_format": preferred_format,
                    "has_video_content": has_video,
                    "has_image_content": has_image,
                    "has_audio_content": has_audio,
                    "related_content": related_content,
                    "timestamp": datetime.now().isoformat(),
                    "neural_enhanced": use_neural_network
                }
                
                return response_data
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao analisar consulta: {str(e)}")
        
        @self.app.post("/api/feedback")
        async def submit_feedback(
            user_id: str = Form(..., description="ID do usuário"),
            query_id: str = Form(..., description="ID da consulta"),
            feedback: str = Form(..., description="Feedback do usuário (positivo/negativo)")
        ):
            """
            Endpoint para submissão de feedback sobre as respostas.
            """
            try:
                valid_feedback = ["positivo", "negativo"]
                if feedback.lower() not in valid_feedback:
                    raise HTTPException(status_code=400, detail="Feedback inválido. Use 'positivo' ou 'negativo'.")
                
                success = self.prompt_service.store_user_interaction(
                    user_id=user_id,
                    query="",
                    response="",
                    feedback=feedback
                )
                
                if success:
                    return {"status": "success", "message": "Feedback registrado com sucesso"}
                else:
                    return {"status": "warning", "message": "Feedback recebido, mas não pôde ser armazenado"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao processar feedback: {str(e)}")
        
        @self.app.post("/api/index")
        async def index_content(
            background_tasks: BackgroundTasks,
            files: List[UploadFile] = File(..., description="Arquivos a serem indexados")
        ):
            """
            Endpoint para indexação de novos conteúdos.
            """
            try:
                if not files:
                    raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
                
                uploaded_files = []
                errors = []
                
                for file in files:
                    try:
                        file_path = os.path.join(self.upload_dir, file.filename)
                        
                        with open(file_path, "wb") as f:
                            content = await file.read()
                            f.write(content)
                        
                        uploaded_files.append({
                            "filename": file.filename,
                            "path": file_path,
                            "size": len(content)
                        })
                    except Exception as e:
                        errors.append(f"Erro ao processar arquivo {file.filename}: {str(e)}")
                
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
                            elif extension in ['.mp3', '.wav', '.ogg', '.aac', '.m4a', '.flac']:
                                self.indexer_service.index_audio(file_path)
                            else:
                                errors.append(f"Tipo de arquivo não suportado: {filename}")
                        except Exception as e:
                            errors.append(f"Erro ao indexar {filename}: {str(e)}")
                
                background_tasks.add_task(index_uploaded_files)
                
                return {
                    "success": True,
                    "message": "Arquivos enviados com sucesso. A indexação está em andamento.",
                    "uploaded_files": [file["filename"] for file in uploaded_files]
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao processar upload: {str(e)}")
        
        @self.app.get("/api/document/{document_id}")
        async def get_document(document_id: str):
            """
            Endpoint para obter um documento específico pelo ID.
            """
            try:
                document = self.search_service.get_document(document_id)
                
                if not document:
                    raise HTTPException(status_code=404, detail=f"Documento não encontrado: {document_id}")
                
                result = self.search_service.get_content_by_preferred_format(
                    document=document,
                    format_type=document.doc_type.value
                )
                
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao recuperar documento: {str(e)}") 