from typing import List, Dict, Any, Optional

from ..interfaces.prompt_service import PromptService


class GenerateAdaptiveResponseUseCase:
    """
    Caso de uso para geração de respostas adaptativas.
    Encapsula a lógica de geração de respostas personalizadas com base no perfil do usuário.
    """
    
    def __init__(self, prompt_service: PromptService, neural_service=None):
        """
        Inicializa o caso de uso com um serviço de prompt.
        
        Args:
            prompt_service: Implementação concreta de um serviço de prompt
            neural_service: Serviço opcional de rede neural para classificação de conteúdo
        """
        self.prompt_service = prompt_service
        self.neural_service = neural_service
        
    def generate_response(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        preferred_format: str = "texto",
        user_id: Optional[str] = None
    ) -> str:
        """
        Gera uma resposta adaptativa com base na consulta e no perfil do usuário.
        
        Args:
            query: Dúvida ou pergunta do usuário
            user_level: Nível de conhecimento do usuário (iniciante, intermediário, avançado)
            preferred_format: Formato preferido de conteúdo (texto, vídeo, imagem, áudio)
            user_id: Identificador opcional do usuário para personalização
            
        Returns:
            Resposta formatada e adaptada ao perfil do usuário
        """
        # Validação dos parâmetros
        if not query.strip():
            return "Por favor, forneça uma pergunta ou dúvida para que eu possa ajudar."
            
        # Validação do nível do usuário
        valid_levels = ["iniciante", "intermediário", "avançado"]
        if user_level.lower() not in valid_levels:
            user_level = "intermediário"  # Nível padrão
            
        # Validação do formato preferido
        valid_formats = ["texto", "vídeo", "imagem", "áudio"]
        if preferred_format.lower() not in valid_formats:
            preferred_format = "texto"  # Formato padrão
            
        # Delega a geração da resposta para o prompt_service
        response = self.prompt_service.generate_response(
            query=query,
            user_level=user_level.lower(),
            preferred_format=preferred_format.lower(),
            user_id=user_id
        )
        
        # Armazena a interação se um user_id for fornecido
        if user_id:
            self.prompt_service.store_user_interaction(
                user_id=user_id,
                query=query,
                response=response
            )
            
            # Se o serviço neural estiver disponível, treina o modelo com esta interação
            if self.neural_service:
                try:
                    # Treina o modelo com base nos feedbacks acumulados
                    self.neural_service.train_from_feedback(user_id)
                except Exception as e:
                    print(f"Erro ao treinar modelo neural: {e}")
            
        return response
        
    def suggest_related_content(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        limit: int = 3,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Sugere conteúdos relacionados com base na consulta e no nível do usuário.
        
        Args:
            query: Dúvida ou pergunta do usuário
            user_level: Nível de conhecimento do usuário
            limit: Número máximo de sugestões
            user_id: Identificador opcional do usuário para personalização
            
        Returns:
            Lista de dicionários com informações sobre os conteúdos relacionados
        """
        # Validação do nível do usuário
        valid_levels = ["iniciante", "intermediário", "avançado"]
        if user_level.lower() not in valid_levels:
            user_level = "intermediário"  # Nível padrão
            
        # Delega a sugestão de conteúdos para o prompt_service
        related_content = self.prompt_service.suggest_related_content(
            query=query,
            user_level=user_level.lower(),
            limit=limit
        )
        
        # Se o serviço neural estiver disponível e tivermos um ID de usuário,
        # usa o modelo para personalizar as sugestões
        if self.neural_service and user_id:
            try:
                # Reordena os conteúdos relacionados com base nas preferências do usuário
                # Isso requer acesso aos documentos originais, que não temos aqui
                # Portanto, faremos apenas um ajuste simples baseado nos títulos
                
                # Simulação da personalização (numa implementação real, esta lógica seria mais complexa)
                if related_content:
                    # Aqui poderia haver uma lógica mais avançada para reordenar o conteúdo
                    # baseada no modelo neural do usuário
                    pass
                    
            except Exception as e:
                print(f"Erro ao personalizar sugestões: {e}")
                
        return related_content 