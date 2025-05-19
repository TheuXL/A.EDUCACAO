import uuid
from typing import List, Optional

class UserSession:
    """
    Classe para gerenciar a sessão do usuário.
    
    Esta classe mantém o estado da sessão de um usuário,
    incluindo suas preferências, histórico de consultas e respostas.
    """
    def __init__(self, user_id: Optional[str] = None):
        """
        Inicializa uma nova sessão de usuário.
        
        Args:
            user_id: ID do usuário. Se não for fornecido, um UUID será gerado.
        """
        if not user_id:
            self.user_id = str(uuid.uuid4())
        else:
            self.user_id = user_id
            
        self.user_level = "intermediário"
        self.preferred_format = "texto"
        self.last_query = ""
        self.last_response = ""
        self.context: List[str] = []  # Histórico de consultas para manter contexto
        
    def update_preferences(self, level: Optional[str] = None, format: Optional[str] = None) -> None:
        """
        Atualiza as preferências do usuário.
        
        Args:
            level: Nível de conhecimento do usuário (iniciante, intermediário, avançado)
            format: Formato preferido de conteúdo (texto, vídeo, imagem)
        """
        if level:
            self.user_level = level
        if format:
            self.preferred_format = format
            
    def add_to_context(self, query: str) -> None:
        """
        Adiciona uma consulta ao contexto da sessão.
        
        Args:
            query: A consulta realizada pelo usuário
        """
        self.last_query = query
        self.context.append(query)
        # Manter apenas as últimas 5 consultas
        if len(self.context) > 5:
            self.context = self.context[-5:]
            
    def get_context(self) -> List[str]:
        """
        Retorna o contexto atual da sessão.
        
        Returns:
            Lista das últimas consultas realizadas pelo usuário
        """
        return self.context
    
    def store_response(self, response: str) -> None:
        """
        Armazena a resposta mais recente.
        
        Args:
            response: A resposta fornecida ao usuário
        """
        self.last_response = response 