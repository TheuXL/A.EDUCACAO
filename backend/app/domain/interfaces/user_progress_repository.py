from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.user_progress import UserProgress


class UserProgressRepository(ABC):
    """
    Interface para repositório de progresso do usuário.
    Define o contrato para armazenamento e recuperação de dados de progresso do usuário.
    """
    
    @abstractmethod
    def save(self, user_progress: UserProgress) -> bool:
        """
        Salva o progresso do usuário no repositório.
        
        Args:
            user_progress: Dados do progresso do usuário a serem salvos
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[UserProgress]:
        """
        Recupera o progresso de um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Progresso do usuário se encontrado, None caso contrário
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[UserProgress]:
        """
        Recupera o progresso de todos os usuários.
        
        Returns:
            Lista com o progresso de todos os usuários
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """
        Remove o progresso de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def update_interaction(self, user_id: str, query: str, response: str, feedback: Optional[str] = None) -> bool:
        """
        Adiciona uma nova interação ao histórico do usuário.
        
        Args:
            user_id: ID do usuário
            query: Consulta realizada pelo usuário
            response: Resposta fornecida pelo sistema
            feedback: Feedback opcional do usuário sobre a resposta
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        pass 