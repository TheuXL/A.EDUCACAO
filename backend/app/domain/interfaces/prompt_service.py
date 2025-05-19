from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class PromptService(ABC):
    """
    Interface para o serviço de geração de respostas adaptativas.
    Define o contrato para todas as implementações de serviços de prompt.
    """
    
    @abstractmethod
    def generate_response(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        preferred_format: str = "texto",
        user_id: Optional[str] = None
    ) -> str:
        """
        Gera uma resposta adaptativa com base na consulta do usuário.
        
        Args:
            query: Dúvida ou pergunta do usuário
            user_level: Nível de conhecimento do usuário (iniciante, intermediário, avançado)
            preferred_format: Formato preferido de conteúdo (texto, vídeo, imagem, áudio)
            user_id: Identificador opcional do usuário para personalização
            
        Returns:
            Resposta formatada com base nos documentos relevantes encontrados
        """
        pass
    
    @abstractmethod
    def suggest_related_content(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Sugere conteúdos relacionados com base na consulta do usuário.
        
        Args:
            query: Dúvida ou pergunta do usuário
            user_level: Nível de conhecimento do usuário
            limit: Número máximo de sugestões
            
        Returns:
            Lista de dicionários com informações sobre os conteúdos relacionados
        """
        pass
    
    @abstractmethod
    def store_user_interaction(
        self, 
        user_id: str, 
        query: str, 
        response: str, 
        feedback: Optional[str] = None
    ) -> bool:
        """
        Armazena a interação do usuário para personalização futura.
        
        Args:
            user_id: Identificador do usuário
            query: Consulta realizada pelo usuário
            response: Resposta fornecida pelo sistema
            feedback: Feedback opcional do usuário sobre a resposta
            
        Returns:
            True se a interação foi armazenada com sucesso, False caso contrário
        """
        pass 