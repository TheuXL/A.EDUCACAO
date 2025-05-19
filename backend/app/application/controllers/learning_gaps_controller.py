from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.domain.interfaces.learning_gap_analyzer import LearningGapAnalyzer
from backend.app.application.services.learning_gap_service import LearningGapServiceImpl
from backend.app.domain.interfaces.user_progress_repository import UserProgressRepository
from backend.app.domain.interfaces.search_service import SearchService


# Definir modelos Pydantic para validação de dados
class GapAnalysisResponse(BaseModel):
    user_id: str
    status: str
    analysis_date: Optional[str] = None
    overall_progress: Optional[float] = None
    engagement_metrics: Optional[Dict[str, Any]] = None
    identified_gaps: List[Dict[str, Any]] = []
    improvement_suggestions: Optional[List[Dict[str, Any]]] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    message: Optional[str] = None


class ImprovementPlanResponse(BaseModel):
    user_id: str
    status: str
    creation_date: Optional[str] = None
    recommended_completion_date: Optional[str] = None
    plan_title: Optional[str] = None
    steps: List[Dict[str, Any]] = []
    overall_goal: Optional[str] = None
    message: Optional[str] = None


class UserStrengthsWeaknessesUpdateRequest(BaseModel):
    user_id: str


class LearningGapsController:
    """
    Controlador para endpoints relacionados a lacunas de aprendizado e planos de melhoria.
    """
    
    def __init__(
        self, 
        user_repository: UserProgressRepository,
        search_service: SearchService
    ):
        """
        Inicializa o controlador com os serviços necessários.
        
        Args:
            user_repository: Repositório para acesso ao progresso do usuário
            search_service: Serviço de busca para encontrar conteúdo relevante
        """
        self.router = APIRouter(prefix="/api/learning", tags=["learning"])
        self.user_repository = user_repository
        self.search_service = search_service
        
        self.gap_analyzer: LearningGapAnalyzer = LearningGapServiceImpl(
            user_repository=user_repository,
            search_service=search_service
        )
        
        self._register_routes()

    def _register_routes(self):
        """
        Registra as rotas do controlador.
        """
        @self.router.get(
            "/analysis/{user_id}", 
            response_model=GapAnalysisResponse,
            summary="Analisa lacunas de conhecimento do usuário",
            description="Analisa o histórico de interações do usuário para identificar lacunas de conhecimento, pontos fortes e fracos"
        )
        async def analyze_learning_gaps(user_id: str):
            try:
                if not user_id:
                    raise HTTPException(status_code=400, detail="ID de usuário é obrigatório")
                
                analysis = self.gap_analyzer.analyze_progress(user_id)
                
                if not analysis.get("identified_gaps") and not analysis.get("strengths"):
                    gap_topics = self._find_gap_topics_in_resources(user_id)
                    if gap_topics:
                        analysis["identified_gaps"] = gap_topics
                
                return analysis
            
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Erro ao analisar lacunas de conhecimento: {str(e)}"
                )
        
        @self.router.get(
            "/improvement-plan/{user_id}",
            response_model=ImprovementPlanResponse,
            summary="Gera um plano de melhoria para o usuário",
            description="Cria um plano de melhoria personalizado com base nas lacunas de conhecimento identificadas"
        )
        async def generate_improvement_plan(user_id: str):
            try:
                if not user_id:
                    raise HTTPException(status_code=400, detail="ID de usuário é obrigatório")
                
                plan = self.gap_analyzer.generate_improvement_plan(user_id)
                
                if not plan.get("steps") or len(plan.get("steps", [])) == 0:
                    resources = self._find_learning_resources(user_id)
                    if resources:
                        plan["steps"] = resources
                        plan["status"] = "success"
                        plan["message"] = "Plano de melhoria gerado com base nos recursos disponíveis"
                
                return plan
            
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Erro ao gerar plano de melhoria: {str(e)}"
                )
        
        @self.router.post(
            "/update-profile",
            summary="Atualiza pontos fortes e fracos no perfil",
            description="Analisa o histórico do usuário e atualiza automaticamente os pontos fortes e fracos no perfil"
        )
        async def update_strengths_weaknesses(request: UserStrengthsWeaknessesUpdateRequest):
            try:
                user_id = request.user_id
                
                if not user_id:
                    raise HTTPException(status_code=400, detail="ID de usuário é obrigatório")
                
                success = self.gap_analyzer.update_user_strengths_weaknesses(user_id)
                
                if not success:
                    strengths, weaknesses = self._find_strengths_weaknesses_in_resources(user_id)
                    
                    if strengths or weaknesses:
                        user_progress = self.user_repository.get_by_id(user_id)
                        if user_progress:
                            if strengths:
                                user_progress.profile.strengths = strengths
                            if weaknesses:
                                user_progress.profile.weaknesses = weaknesses
                            self.user_repository.save(user_progress)
                            success = True
                    
                    if not success:
                        return {
                            "status": "error",
                            "message": "Não foi possível atualizar o perfil ou usuário não encontrado"
                        }
                
                user_progress = self.user_repository.get_by_id(user_id)
                
                if not user_progress:
                    return {
                        "status": "error",
                        "message": "Usuário não encontrado após atualização"
                    }
                
                return {
                    "status": "success",
                    "message": "Perfil atualizado com sucesso",
                    "strengths": user_progress.profile.strengths,
                    "weaknesses": user_progress.profile.weaknesses
                }
            
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Erro ao atualizar perfil: {str(e)}"
                )
    
    def _find_gap_topics_in_resources(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Busca tópicos nos recursos que podem representar lacunas de conhecimento.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de lacunas identificadas nos recursos
        """
        try:
            user_progress = self.user_repository.get_by_id(user_id)
            if not user_progress:
                return []
                
            topics = []
            for interaction in user_progress.interactions:
                query_topics = self.gap_analyzer._extract_topics(interaction.query)
                topics.extend(query_topics)
            
            gaps = []
            for topic in set(topics):
                results = self.search_service.search(topic, limit=2)
                if not results:
                    gaps.append({
                        "topic": topic,
                        "severity": "média",
                        "confidence": 0.7,
                        "suggestions": [f"Aprofundar conhecimento em {topic}"]
                    })
            
            if not gaps:
                html_topics = ["HTML5", "elementos semânticos", "formulários", "CSS", "JavaScript"]
                for topic in html_topics:
                    results = self.search_service.search(topic, limit=1)
                    if results:
                        gaps.append({
                            "topic": topic,
                            "severity": "baixa",
                            "confidence": 0.5,
                            "suggestions": [f"Estudar conceitos básicos de {topic}"]
                        })
            
            return gaps[:3]
            
        except Exception as e:
            print(f"Erro ao buscar lacunas nos recursos: {e}")
            return []
    
    def _find_learning_resources(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Busca recursos de aprendizagem relevantes para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de recursos formatados como passos de um plano de melhoria
        """
        try:
            user_progress = self.user_repository.get_by_id(user_id)
            if not user_progress:
                return []
            
            topics = user_progress.profile.interests.copy() if user_progress.profile.interests else []
            
            if user_progress.profile.weaknesses:
                topics.extend(user_progress.profile.weaknesses)
            
            if not topics:
                topics = ["HTML5", "estrutura de página web", "formatação de texto", "listas", "tabelas"]
            
            resources = []
            for i, topic in enumerate(topics):
                results = self.search_service.search(topic, limit=1)
                if results and len(results) > 0:
                    doc = results[0]
                    resources.append({
                        "id": f"step_{i+1}",
                        "title": f"Aprendizado sobre {topic}",
                        "description": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        "resource_type": doc.doc_type.value,
                        "estimated_time": "30 minutos",
                        "difficulty": "intermediário"
                    })
            
            return resources
            
        except Exception as e:
            print(f"Erro ao buscar recursos de aprendizagem: {e}")
            return []
    
    def _find_strengths_weaknesses_in_resources(self, user_id: str) -> tuple[List[str], List[str]]:
        """
        Busca pontos fortes e fracos com base nos recursos disponíveis.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Tupla com (pontos fortes, pontos fracos)
        """
        try:
            user_progress = self.user_repository.get_by_id(user_id)
            if not user_progress:
                return [], []
            
            strengths = []
            weaknesses = []
            
            html_topics = [
                "estrutura HTML5", "elementos semânticos", "formatação de texto", 
                "listas", "tabelas", "formulários", "CSS", "JavaScript"
            ]
            
            for interaction in user_progress.interactions:
                for topic in html_topics:
                    if topic.lower() in interaction.query.lower():
                        if interaction.feedback == "positivo":
                            strengths.append(topic)
                        elif interaction.feedback == "negativo":
                            weaknesses.append(topic)
            
            if not strengths and not weaknesses:
                for i, topic in enumerate(html_topics):
                    if i % 2 == 0 and len(strengths) < 3:
                        strengths.append(topic)
                    elif len(weaknesses) < 3:
                        weaknesses.append(topic)
            
            return list(set(strengths)), list(set(weaknesses))
            
        except Exception as e:
            print(f"Erro ao buscar pontos fortes e fracos: {e}")
            return [], []
    
    def get_router(self) -> APIRouter:
        """
        Retorna o router do controlador.
        
        Returns:
            Router do FastAPI com os endpoints registrados
        """
        return self.router 