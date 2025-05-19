from typing import Optional, Dict, Any, List
import json
import os
from datetime import datetime

from app.domain.interfaces.user_progress_repository import UserProgressRepository
from app.domain.entities.user_progress import UserProgress, UserProfile, UserInteraction


class JsonUserProgressRepository(UserProgressRepository):
    """
    Implementação do repositório de progresso do usuário utilizando JSON.
    """
    
    def __init__(self, json_file_path: Optional[str] = None):
        """
        Inicializa o repositório JSON.
        
        Args:
            json_file_path: Caminho para o arquivo JSON. Se não for fornecido,
                           um arquivo padrão será criado no diretório database.
        """
        # Define o caminho do arquivo JSON
        if json_file_path:
            self.json_file = json_file_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.json_file = os.path.join(base_dir, "database", "user_progress.json")
        
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
        
        # Inicializa o arquivo JSON se não existir
        if not os.path.exists(self.json_file):
            with open(self.json_file, "w") as f:
                json.dump({}, f)
                
    def get_by_id(self, user_id: str) -> Optional[UserProgress]:
        """
        Recupera o progresso de um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            UserProgress se encontrado, None caso contrário
        """
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
                
            if user_id not in data:
                return None
                
            user_data = data[user_id]
            return UserProgress.from_dict(user_data)
            
        except Exception as e:
            print(f"Erro ao ler arquivo JSON: {e}")
            return None
    
    def get_all(self) -> List[UserProgress]:
        """
        Recupera o progresso de todos os usuários.
        
        Returns:
            Lista com o progresso de todos os usuários
        """
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
                
            result = []
            for user_id, user_data in data.items():
                user_data["user_id"] = user_id
                user_progress = UserProgress.from_dict(user_data)
                result.append(user_progress)
                
            return result
            
        except Exception as e:
            print(f"Erro ao ler arquivo JSON: {e}")
            return []
            
    def delete(self, user_id: str) -> bool:
        """
        Remove o progresso de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        try:
            # Lê o arquivo
            with open(self.json_file, "r") as f:
                data = json.load(f)
                
            # Verifica se o usuário existe
            if user_id not in data:
                return False
                
            # Remove o usuário
            del data[user_id]
            
            # Salva o arquivo
            with open(self.json_file, "w") as f:
                json.dump(data, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Erro ao remover usuário do arquivo JSON: {e}")
            return False
            
    def save(self, user_progress: UserProgress) -> bool:
        """
        Salva o progresso do usuário.
        
        Args:
            user_progress: Objeto UserProgress a ser salvo
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        try:
            # Lê o arquivo
            with open(self.json_file, "r") as f:
                data = json.load(f)
                
            # Atualiza os dados
            data[user_progress.user_id] = user_progress.to_dict()
            
            # Salva o arquivo
            with open(self.json_file, "w") as f:
                json.dump(data, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Erro ao salvar no arquivo JSON: {e}")
            return False
            
    def update_interaction(
        self, 
        user_id: str, 
        query: str, 
        response: str, 
        feedback: Optional[str] = None
    ) -> bool:
        """
        Atualiza as interações do usuário.
        
        Args:
            user_id: ID do usuário
            query: Consulta realizada pelo usuário
            response: Resposta fornecida pelo sistema
            feedback: Feedback opcional do usuário sobre a resposta
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        # Recupera o progresso do usuário
        user_progress = self.get_by_id(user_id)
        
        # Se não existir, cria um novo
        if not user_progress:
            user_progress = UserProgress(
                user_id=user_id
            )
            
        # Adiciona a interação
        user_progress.add_interaction(query, response, feedback)
        
        # Salva o progresso
        return self.save(user_progress) 