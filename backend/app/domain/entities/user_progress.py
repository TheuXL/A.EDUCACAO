from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class UserInteraction:
    """
    Representa uma interação do usuário com o sistema.
    """
    query: str
    response: str
    timestamp: datetime = field(default_factory=datetime.now)
    feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a interação para um dicionário."""
        return {
            "query": self.query,
            "response": self.response,
            "timestamp": self.timestamp.isoformat(),
            "feedback": self.feedback
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInteraction':
        """Cria uma instância a partir de um dicionário."""
        return cls(
            query=data["query"],
            response=data["response"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            feedback=data.get("feedback")
        )


@dataclass
class UserProfile:
    """
    Perfil do usuário com suas preferências e nível de conhecimento.
    """
    level: str = "intermediário"
    preferred_format: str = "texto"
    interests: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o perfil para um dicionário."""
        return {
            "level": self.level,
            "preferred_format": self.preferred_format,
            "interests": self.interests,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Cria uma instância a partir de um dicionário."""
        return cls(
            level=data.get("level", "intermediário"),
            preferred_format=data.get("preferred_format", "texto"),
            interests=data.get("interests", []),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", [])
        )


@dataclass
class UserProgress:
    """
    Representa o progresso e histórico de interações de um usuário.
    """
    user_id: str
    profile: UserProfile = field(default_factory=UserProfile)
    interactions: List[UserInteraction] = field(default_factory=list)
    last_interaction: Optional[datetime] = None
    
    def add_interaction(self, query: str, response: str, feedback: Optional[str] = None) -> None:
        """
        Adiciona uma nova interação ao histórico do usuário.
        
        Args:
            query: Consulta realizada pelo usuário
            response: Resposta fornecida pelo sistema
            feedback: Feedback opcional do usuário sobre a resposta
        """
        interaction = UserInteraction(query=query, response=response, feedback=feedback)
        self.interactions.append(interaction)
        self.last_interaction = interaction.timestamp
        
    def update_profile(
        self, 
        level: Optional[str] = None, 
        preferred_format: Optional[str] = None,
        interests: Optional[List[str]] = None,
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None
    ) -> None:
        """
        Atualiza o perfil do usuário.
        
        Args:
            level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            interests: Lista de interesses do usuário
            strengths: Lista de pontos fortes do usuário
            weaknesses: Lista de pontos fracos do usuário
        """
        if level:
            self.profile.level = level
        if preferred_format:
            self.profile.preferred_format = preferred_format
        if interests:
            self.profile.interests = interests
        if strengths:
            self.profile.strengths = strengths
        if weaknesses:
            self.profile.weaknesses = weaknesses
            
    def get_recent_interactions(self, limit: int = 5) -> List[UserInteraction]:
        """
        Obtém as interações mais recentes do usuário.
        
        Args:
            limit: Número máximo de interações a serem retornadas
            
        Returns:
            Lista das interações mais recentes
        """
        # Ordena as interações por timestamp (mais recentes primeiro) e limita o número
        return sorted(
            self.interactions, 
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
        
    def calculate_engagement_metrics(self) -> Dict[str, Any]:
        """
        Calcula métricas de engajamento do usuário.
        
        Returns:
            Dicionário com métricas de engajamento
        """
        if not self.interactions:
            return {
                "total_interactions": 0,
                "avg_interactions_per_day": 0,
                "topics_explored": [],
                "feedback_ratio": 0,
                "last_active_days_ago": None
            }
        
        # Total de interações
        total_interactions = len(self.interactions)
        
        # Calcula média de interações por dia
        if total_interactions >= 2:
            first_interaction = min(self.interactions, key=lambda x: x.timestamp)
            last_interaction = max(self.interactions, key=lambda x: x.timestamp)
            days_diff = (last_interaction.timestamp - first_interaction.timestamp).days
            avg_per_day = total_interactions / max(1, days_diff)
        else:
            avg_per_day = total_interactions
        
        # Extrai tópicos exclusivos explorados
        all_queries = " ".join([interaction.query for interaction in self.interactions])
        topics = set()
        
        # Palavras-chave comuns em consultas (para filtrar)
        common_keywords = ["como", "o que", "qual", "quando", "onde", "por que", "quem", 
                           "para", "que", "de", "da", "do", "em", "por", "com", "no", "na"]
        
        for word in all_queries.lower().split():
            if len(word) > 3 and word not in common_keywords:
                topics.add(word)
        
        # Calcula proporção de feedback
        feedback_count = sum(1 for interaction in self.interactions if interaction.feedback)
        feedback_ratio = feedback_count / total_interactions if total_interactions > 0 else 0
        
        # Calcula dias desde última atividade
        if self.last_interaction:
            last_active_days = (datetime.now() - self.last_interaction).days
        else:
            last_active_days = None
        
        return {
            "total_interactions": total_interactions,
            "avg_interactions_per_day": round(avg_per_day, 2),
            "topics_explored": list(topics)[:10],  # Limita a 10 tópicos
            "feedback_ratio": round(feedback_ratio, 2),
            "last_active_days_ago": last_active_days,
            "engagement_score": self._calculate_engagement_score(total_interactions, feedback_ratio)
        }
    
    def _calculate_engagement_score(self, total_interactions: int, feedback_ratio: float) -> int:
        """
        Calcula uma pontuação de engajamento baseada nas interações e feedback.
        
        Args:
            total_interactions: Número total de interações
            feedback_ratio: Proporção de interações com feedback
            
        Returns:
            Pontuação de engajamento (0-100)
        """
        # Pontuação baseada no número de interações (máx 60 pontos)
        interaction_score = min(60, total_interactions * 5)
        
        # Pontuação baseada no feedback (máx 40 pontos)
        feedback_score = int(feedback_ratio * 40)
        
        # Pontuação total (máx 100 pontos)
        return interaction_score + feedback_score
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte o progresso do usuário para um dicionário."""
        return {
            "user_id": self.user_id,
            "profile": self.profile.to_dict(),
            "interactions": [interaction.to_dict() for interaction in self.interactions],
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProgress':
        """Cria uma instância a partir de um dicionário."""
        profile = UserProfile.from_dict(data.get("profile", {}))
        
        interactions = []
        for interaction_data in data.get("interactions", []):
            interactions.append(UserInteraction.from_dict(interaction_data))
            
        instance = cls(
            user_id=data["user_id"],
            profile=profile,
            interactions=interactions
        )
        
        if data.get("last_interaction"):
            instance.last_interaction = datetime.fromisoformat(data["last_interaction"])
            
        return instance 