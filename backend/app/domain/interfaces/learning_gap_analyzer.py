from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.app.domain.entities.user_progress import UserProgress


class LearningGapAnalyzer(ABC):
    """
    Interface para analisadores de lacunas de aprendizado.
    Responsável por identificar lacunas de conhecimento com base no histórico de interações do usuário.
    """
    
    @abstractmethod
    def analyze_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Analisa o progresso do usuário para identificar padrões e lacunas.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com análise detalhada do progresso, incluindo lacunas identificadas
        """
        pass
    
    @abstractmethod
    def identify_gaps(self, user_progress: UserProgress) -> List[Dict[str, Any]]:
        """
        Identifica lacunas específicas no conhecimento do usuário.
        
        Args:
            user_progress: Objeto com o progresso do usuário
            
        Returns:
            Lista de lacunas identificadas com metadados (tópico, nível, sugestões)
        """
        pass
    
    @abstractmethod
    def generate_improvement_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Gera um plano de melhoria para preencher as lacunas identificadas.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Plano de melhoria com passos recomendados e recursos
        """
        pass
    
    @abstractmethod
    def update_user_strengths_weaknesses(self, user_id: str) -> bool:
        """
        Atualiza os pontos fortes e fracos no perfil do usuário com base nas análises.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        pass 