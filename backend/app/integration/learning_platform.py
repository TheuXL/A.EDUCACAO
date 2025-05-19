import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import uuid
from datetime import datetime
import logging

from backend.app.application.services.indexer_service import IndexerService
from backend.app.application.services.prompt_service import PromptServiceImpl
from backend.app.application.services.learning_gap_service import LearningGapServiceImpl
from backend.app.domain.usecases.generate_adaptive_response_usecase import GenerateAdaptiveResponseUseCase
from backend.app.infrastructure.repositories.json_user_progress_repository import JsonUserProgressRepository
from backend.app.infrastructure.repositories.chroma_document_repository import ChromaDocumentRepository


class LearningPlatform:
    """
    Classe de integração que combina todos os serviços do sistema A.EDUCAÇÃO
    em um único ponto de entrada para facilitar o uso da plataforma.
    
    Esta classe oferece métodos para:
    - Indexar conteúdo (texto, PDF, vídeo, imagem)
    - Gerar respostas adaptativas
    - Analisar lacunas de conhecimento
    - Gerar planos de melhoria personalizados
    - Monitorar progresso do usuário
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Inicializa a plataforma de aprendizado configurando todos os serviços necessários.
        
        Args:
            base_dir: Diretório base para armazenamento de arquivos, 
                     por padrão usa o diretório backend no projeto.
        """
        # Configura o logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("A.EDUCACAO")
        
        # Define diretórios de trabalho
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        
        # Configura diretórios necessários
        self._setup_directories()
        
        # Inicializa repositórios
        self.logger.info("Inicializando repositórios...")
        self.user_repository = JsonUserProgressRepository(
            json_file_path=str(self.data_dir / "user_progress.json")
        )
        
        # Inicializa o ChromaDB
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_dir))
            self.document_repository = ChromaDocumentRepository(
                chroma_client=self.chroma_client,
                collection_name="a_educacao"
            )
        except ImportError:
            self.logger.warning(
                "ChromaDB não encontrado! Funcionalidade de indexação e busca não estará disponível. "
                "Instale com: pip install chromadb"
            )
            self.chroma_client = None
            self.document_repository = None
        
        # Inicializa o serviço de indexação
        if self.document_repository:
            self.indexer_service = IndexerService(
                chroma_client=self.chroma_client,
                collection_name="a_educacao",
                user_progress_repository=self.user_repository
            )
            self.search_service = self.indexer_service.search_service
        else:
            self.indexer_service = None
            self.search_service = None
        
        # Inicializa o serviço de prompts
        if self.search_service:
            self.prompt_service = PromptServiceImpl(
                search_service=self.search_service,
                user_progress_repository=self.user_repository
            )
            
            # Inicializa o caso de uso de resposta adaptativa
            self.adaptive_response_usecase = GenerateAdaptiveResponseUseCase(
                prompt_service=self.prompt_service,
                neural_service=self.indexer_service.neural_network_service if self.indexer_service else None
            )
        else:
            self.prompt_service = None
            self.adaptive_response_usecase = None
        
        # Inicializa o serviço de análise de lacunas
        if self.user_repository:
            self.learning_gap_service = LearningGapServiceImpl(
                user_repository=self.user_repository,
                search_service=self.search_service
            )
        else:
            self.learning_gap_service = None
            
        self.logger.info("A.EDUCAÇÃO inicializado com sucesso!")
        
    def _setup_directories(self):
        """
        Configura os diretórios necessários para o sistema.
        """
        # Diretórios principais
        self.data_dir = self.base_dir / "database"
        self.resources_dir = self.base_dir / "resources"
        self.uploads_dir = self.base_dir / "uploads"
        self.models_dir = self.base_dir / "models"
        self.chroma_dir = self.data_dir / "chromadb"
        self.logs_dir = self.base_dir / "logs"
        
        # Cria os diretórios se não existirem
        for directory in [
            self.data_dir, self.resources_dir, self.uploads_dir,
            self.models_dir, self.chroma_dir, self.logs_dir
        ]:
            os.makedirs(directory, exist_ok=True)
    
    def index_content(self, path: str) -> Dict[str, Any]:
        """
        Indexa conteúdo a partir de um arquivo ou diretório.
        
        Args:
            path: Caminho do arquivo ou diretório a ser indexado
            
        Returns:
            Dicionário com o status da indexação
        """
        if not self.indexer_service:
            return {
                "success": False,
                "message": "Serviço de indexação não está disponível",
                "details": "Verifique se o ChromaDB está instalado"
            }
        
        path_obj = Path(path)
        
        try:
            if path_obj.is_dir():
                self.logger.info(f"Indexando diretório: {path}")
                success = self.indexer_service.index_directory(path_obj)
                message = "Diretório indexado com sucesso" if success else "Erro ao indexar diretório"
            elif path_obj.is_file():
                self.logger.info(f"Indexando arquivo: {path}")
                success = self.indexer_service.index_file(path_obj)
                message = "Arquivo indexado com sucesso" if success else "Erro ao indexar arquivo"
            else:
                return {
                    "success": False,
                    "message": "Caminho não encontrado",
                    "details": f"O caminho {path} não existe ou não é acessível"
                }
            
            return {
                "success": success,
                "message": message,
                "path": str(path_obj)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao indexar {path}: {str(e)}")
            return {
                "success": False,
                "message": "Erro durante indexação",
                "details": str(e)
            }
    
    def search_content(
        self, 
        query: str, 
        limit: int = 5, 
        doc_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca conteúdo relacionado à consulta.
        
        Args:
            query: Consulta de busca
            limit: Número máximo de resultados
            doc_type: Tipo de documento a ser filtrado (opcional)
            user_id: ID do usuário para personalização (opcional)
            
        Returns:
            Dicionário com os resultados da busca
        """
        if not self.search_service:
            return {
                "success": False,
                "message": "Serviço de busca não está disponível",
                "results": []
            }
        
        try:
            # Busca com personalização se um ID de usuário for fornecido
            if user_id and self.indexer_service.neural_network_service:
                docs = self.indexer_service.search_with_neural_ranking(query, user_id, limit)
                neural_enhanced = True
            # Busca por tipo de documento
            elif doc_type:
                docs = self.search_service.search_by_type(query, doc_type, limit)
                neural_enhanced = False
            # Busca padrão
            else:
                docs = self.search_service.search(query, limit)
                neural_enhanced = False
            
            # Formata os resultados
            results = []
            for doc in docs:
                result = {
                    "id": doc.id,
                    "type": doc.doc_type.value,
                    "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "metadata": doc.metadata if doc.metadata else {}
                }
                results.append(result)
            
            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": results,
                "neural_enhanced": neural_enhanced
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar por '{query}': {str(e)}")
            return {
                "success": False,
                "message": f"Erro durante busca: {str(e)}",
                "results": []
            }
    
    def generate_response(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        preferred_format: str = "texto",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera uma resposta adaptativa para a consulta do usuário.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            user_id: ID do usuário (opcional)
            
        Returns:
            Dicionário com a resposta e informações relacionadas
        """
        if not self.adaptive_response_usecase:
            return {
                "success": False,
                "message": "Serviço de resposta adaptativa não está disponível",
                "response": f"Não foi possível processar sua consulta: '{query}'. O serviço de resposta não está disponível."
            }
        
        try:
            # Gera um ID de usuário se não for fornecido
            if not user_id:
                user_id = str(uuid.uuid4())
                
            # Gera ID único para a consulta
            query_id = str(uuid.uuid4())
            
            # Gera a resposta adaptativa
            response = self.adaptive_response_usecase.generate_response(
                query=query,
                user_level=user_level,
                preferred_format=preferred_format,
                user_id=user_id
            )
            
            # Busca conteúdos relacionados
            related_content = self.prompt_service.suggest_related_content(
                query=query,
                user_level=user_level,
                limit=3
            )
            
            # Verifica se a resposta contém indicação de conteúdo em vídeo/imagem
            has_video = "📺" in response and preferred_format == "vídeo"
            has_image = "🖼️" in response and preferred_format == "imagem"
            
            return {
                "success": True,
                "user_id": user_id,
                "query_id": query_id,
                "query": query,
                "response": response,
                "user_level": user_level,
                "preferred_format": preferred_format,
                "has_video_content": has_video,
                "has_image_content": has_image,
                "related_content": related_content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta para '{query}': {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao gerar resposta: {str(e)}",
                "response": f"Não foi possível processar sua consulta: '{query}'. Ocorreu um erro: {str(e)}"
            }
    
    def submit_feedback(
        self, 
        user_id: str, 
        query_id: str, 
        feedback: str
    ) -> Dict[str, Any]:
        """
        Submete feedback sobre uma resposta.
        
        Args:
            user_id: ID do usuário
            query_id: ID da consulta
            feedback: Feedback do usuário
            
        Returns:
            Dicionário com o status do feedback
        """
        if not self.user_repository:
            return {
                "success": False,
                "message": "Repositório de usuários não está disponível"
            }
        
        try:
            # Salva o feedback
            success = self.user_repository.update_interaction(
                user_id=user_id,
                query="",  # Não temos a consulta original aqui
                response="",  # Não temos a resposta original aqui
                feedback=feedback
            )
            
            # Treina o modelo neural se disponível
            neural_updated = False
            if success and self.indexer_service and self.indexer_service.neural_network_service:
                try:
                    loss = self.indexer_service.neural_network_service.train_from_feedback(user_id)
                    neural_updated = True
                except Exception as e:
                    self.logger.warning(f"Erro ao treinar modelo neural: {str(e)}")
            
            return {
                "success": success,
                "message": "Feedback registrado com sucesso" if success else "Erro ao registrar feedback",
                "neural_updated": neural_updated
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar feedback: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao processar feedback: {str(e)}"
            }
    
    def analyze_learning_gaps(self, user_id: str) -> Dict[str, Any]:
        """
        Analisa as lacunas de conhecimento do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com análise de lacunas de conhecimento
        """
        if not self.learning_gap_service:
            return {
                "success": False,
                "message": "Serviço de análise de lacunas não está disponível",
                "user_id": user_id
            }
        
        try:
            # Analisa o progresso do usuário
            analysis = self.learning_gap_service.analyze_progress(user_id)
            
            return {
                "success": True,
                **analysis
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar lacunas para usuário {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao analisar lacunas: {str(e)}",
                "user_id": user_id
            }
    
    def generate_improvement_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Gera um plano de melhoria para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com plano de melhoria
        """
        if not self.learning_gap_service:
            return {
                "success": False,
                "message": "Serviço de análise de lacunas não está disponível",
                "user_id": user_id
            }
        
        try:
            # Gera o plano de melhoria
            plan = self.learning_gap_service.generate_improvement_plan(user_id)
            
            return {
                "success": True,
                **plan
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar plano de melhoria para usuário {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao gerar plano de melhoria: {str(e)}",
                "user_id": user_id
            }
    
    def update_user_profile(
        self, 
        user_id: str, 
        level: Optional[str] = None, 
        preferred_format: Optional[str] = None,
        interests: Optional[List[str]] = None,
        update_strengths_weaknesses: bool = False
    ) -> Dict[str, Any]:
        """
        Atualiza o perfil do usuário.
        
        Args:
            user_id: ID do usuário
            level: Nível de conhecimento do usuário (opcional)
            preferred_format: Formato preferido de conteúdo (opcional)
            interests: Lista de interesses do usuário (opcional)
            update_strengths_weaknesses: Se True, analisa e atualiza pontos fortes e fracos
            
        Returns:
            Dicionário com status da atualização e perfil atualizado
        """
        if not self.user_repository:
            return {
                "success": False,
                "message": "Repositório de usuários não está disponível"
            }
        
        try:
            # Recupera o usuário
            user_progress = self.user_repository.get_by_id(user_id)
            
            # Se o usuário não existir, cria um novo
            if not user_progress:
                from backend.app.domain.entities.user_progress import UserProgress
                user_progress = UserProgress(user_id=user_id)
            
            # Atualiza o perfil com os valores fornecidos
            user_progress.update_profile(
                level=level,
                preferred_format=preferred_format,
                interests=interests
            )
            
            # Se solicitado, atualiza os pontos fortes e fracos com base nas análises
            if update_strengths_weaknesses and self.learning_gap_service:
                self.learning_gap_service.update_user_strengths_weaknesses(user_id)
                
                # Recarrega o usuário para ter os valores atualizados
                user_progress = self.user_repository.get_by_id(user_id)
            
            # Salva as alterações
            success = self.user_repository.save(user_progress)
            
            if success:
                return {
                    "success": True,
                    "message": "Perfil atualizado com sucesso",
                    "user_id": user_id,
                    "profile": {
                        "level": user_progress.profile.level,
                        "preferred_format": user_progress.profile.preferred_format,
                        "interests": user_progress.profile.interests,
                        "strengths": user_progress.profile.strengths,
                        "weaknesses": user_progress.profile.weaknesses
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Erro ao salvar perfil"
                }
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar perfil para usuário {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao atualizar perfil: {str(e)}"
            }
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém o progresso do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com o progresso do usuário
        """
        if not self.user_repository:
            return {
                "success": False,
                "message": "Repositório de usuários não está disponível"
            }
        
        try:
            # Recupera o usuário
            user_progress = self.user_repository.get_by_id(user_id)
            
            if not user_progress:
                return {
                    "success": False,
                    "message": "Usuário não encontrado",
                    "user_id": user_id
                }
            
            # Calcula métricas de engajamento
            engagement_metrics = user_progress.calculate_engagement_metrics()
            
            # Formata interações recentes
            recent_interactions = []
            for interaction in user_progress.get_recent_interactions(5):
                recent_interactions.append({
                    "query": interaction.query,
                    "timestamp": interaction.timestamp.isoformat(),
                    "has_feedback": interaction.feedback is not None
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "profile": {
                    "level": user_progress.profile.level,
                    "preferred_format": user_progress.profile.preferred_format,
                    "interests": user_progress.profile.interests,
                    "strengths": user_progress.profile.strengths,
                    "weaknesses": user_progress.profile.weaknesses
                },
                "engagement_metrics": engagement_metrics,
                "recent_interactions": recent_interactions,
                "interaction_count": len(user_progress.interactions),
                "last_interaction": user_progress.last_interaction.isoformat() if user_progress.last_interaction else None
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter progresso para usuário {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao obter progresso: {str(e)}",
                "user_id": user_id
            }
    
    def get_recommendations(self, user_id: str, limit: int = 5) -> Dict[str, Any]:
        """
        Obtém recomendações personalizadas para o usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de recomendações
            
        Returns:
            Dicionário com recomendações personalizadas
        """
        if not self.prompt_service:
            return {
                "success": False,
                "message": "Serviço de recomendação não está disponível"
            }
        
        try:
            # Obtém o progresso do usuário
            user_progress = self.user_repository.get_by_id(user_id) if self.user_repository else None
            
            if not user_progress:
                # Se não existe progresso, retorna recomendações genéricas
                generic_recommendations = self.prompt_service.suggest_related_content(
                    query="aprendizagem adaptativa",
                    limit=limit
                )
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "is_personalized": False,
                    "recommendations": generic_recommendations
                }
            
            # Obtém recomendações baseadas nas interações do usuário
            # Obtém as consultas recentes do usuário
            recent_interactions = user_progress.get_recent_interactions(5)
            
            if recent_interactions:
                # Combina consultas recentes para gerar recomendações relevantes
                combined_query = " ".join([interaction.query for interaction in recent_interactions[:3]])
                
                # Busca conteúdos relacionados às consultas recentes
                recommendations = self.prompt_service.suggest_related_content(
                    query=combined_query,
                    user_level=user_progress.profile.level,
                    limit=limit
                )
            else:
                # Se não há interações recentes, usa o perfil do usuário
                if user_progress.profile.interests:
                    interests_query = " ".join(user_progress.profile.interests[:3])
                    recommendations = self.prompt_service.suggest_related_content(
                        query=interests_query,
                        user_level=user_progress.profile.level,
                        limit=limit
                    )
                else:
                    # Se não há interesses definidos, usa recomendações genéricas
                    recommendations = self.prompt_service.suggest_related_content(
                        query="aprendizagem adaptativa",
                        user_level=user_progress.profile.level,
                        limit=limit
                    )
            
            return {
                "success": True,
                "user_id": user_id,
                "is_personalized": True,
                "recommendations": recommendations,
                "user_level": user_progress.profile.level,
                "preferred_format": user_progress.profile.preferred_format
            }
                
        except Exception as e:
            self.logger.error(f"Erro ao obter recomendações para usuário {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Erro ao obter recomendações: {str(e)}"
            } 