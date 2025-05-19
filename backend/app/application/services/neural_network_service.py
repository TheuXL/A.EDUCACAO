import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from backend.app.domain.entities.document import Document
from backend.app.domain.interfaces.user_progress_repository import UserProgressRepository


class SimpleNeuralNetwork(nn.Module):
    """
    Rede neural simples para aprendizado adaptativo.
    Perceptron multicamadas (MLP) que aprende com base nos feedbacks dos usuários.
    """
    def __init__(self, input_size, hidden_size, output_size):
        super(SimpleNeuralNetwork, self).__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        out = self.layer1(x)
        out = self.relu(out)
        out = self.layer2(out)
        return out


class NeuralNetworkService:
    """
    Serviço de rede neural para aprendizado adaptativo.
    Responsável por treinar, inferir e atualizar os pesos da rede neural.
    """
    
    def __init__(
        self, 
        user_progress_repository: UserProgressRepository,
        input_size: int = 50, 
        hidden_size: int = 20, 
        output_size: int = 5,
        learning_rate: float = 0.001,
        model_dir: Optional[str] = None
    ):
        """
        Inicializa o serviço de rede neural adaptativa.
        
        Args:
            user_progress_repository: Repositório para acessar o progresso do usuário
            input_size: Tamanho da camada de entrada
            hidden_size: Tamanho da camada oculta
            output_size: Tamanho da camada de saída
            learning_rate: Taxa de aprendizado
            model_dir: Diretório para salvar/carregar o modelo
        """
        self.user_progress_repository = user_progress_repository
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # Define o diretório do modelo
        if model_dir is None:
            base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent
            model_dir = os.path.join(base_dir, "models")
        
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Inicializa o modelo, critério e otimizador
        self.models = {}  # Um modelo para cada usuário
        self.criterion = nn.MSELoss()  # Erro quadrático médio para problemas de regressão
        
        # Dicionário para armazenar o vocabulário de tokens
        self.vocab = {}  # Mapeamento de palavras para índices
        self.vocab_size = 0
        
        # Carrega o vocabulário, se existir
        self._load_vocabulary()
    
    def get_or_create_user_model(self, user_id: str):
        """
        Obtém ou cria um modelo para um usuário específico.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Modelo de rede neural para o usuário
        """
        if user_id not in self.models:
            # Verificar se existe um modelo salvo
            model_path = os.path.join(self.model_dir, f"model_{user_id}.pt")
            
            if os.path.exists(model_path):
                # Carregar modelo existente
                self.models[user_id] = SimpleNeuralNetwork(
                    self.input_size, self.hidden_size, self.output_size
                )
                self.models[user_id].load_state_dict(torch.load(model_path))
                print(f"Modelo carregado para o usuário {user_id}")
            else:
                # Criar novo modelo
                self.models[user_id] = SimpleNeuralNetwork(
                    self.input_size, self.hidden_size, self.output_size
                )
                print(f"Novo modelo criado para o usuário {user_id}")
            
            # Criar otimizador para o modelo
            self.models[user_id].optimizer = optim.Adam(
                self.models[user_id].parameters(), 
                lr=self.learning_rate
            )
        
        return self.models[user_id]
    
    def _text_to_vector(self, text: str) -> torch.Tensor:
        """
        Converte texto em vetor usando a técnica de bag of words.
        
        Args:
            text: Texto a ser convertido
            
        Returns:
            Tensor representando o texto
        """
        # Tokenização simples
        words = text.lower().split()
        
        # Inicializa vetor com zeros
        vector = torch.zeros(self.input_size)
        
        # Atualiza o vetor com as palavras presentes no texto
        for word in words:
            if word in self.vocab:
                idx = self.vocab[word]
                if idx < self.input_size:
                    vector[idx] = 1.0
        
        return vector
    
    def _update_vocabulary(self, text: str):
        """
        Atualiza o vocabulário com novas palavras.
        
        Args:
            text: Texto contendo palavras a serem adicionadas ao vocabulário
        """
        words = text.lower().split()
        
        for word in words:
            if word not in self.vocab:
                self.vocab[word] = self.vocab_size
                self.vocab_size += 1
        
        # Salva o vocabulário atualizado
        self._save_vocabulary()
    
    def _save_vocabulary(self):
        """
        Salva o vocabulário em um arquivo JSON.
        """
        vocab_path = os.path.join(self.model_dir, "vocabulary.json")
        
        with open(vocab_path, "w") as f:
            json.dump(self.vocab, f)
    
    def _load_vocabulary(self):
        """
        Carrega o vocabulário de um arquivo JSON.
        """
        vocab_path = os.path.join(self.model_dir, "vocabulary.json")
        
        if os.path.exists(vocab_path):
            with open(vocab_path, "r") as f:
                self.vocab = json.load(f)
                self.vocab_size = len(self.vocab)
    
    def train_from_feedback(self, user_id: str) -> float:
        """
        Treina o modelo com base nos feedbacks do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Perda (loss) do treinamento
        """
        # Obtém o progresso do usuário
        user_progress = self.user_progress_repository.get_by_id(user_id)
        if not user_progress or not user_progress.interactions:
            return 0.0
            
        # Obtém o modelo do usuário
        model = self.get_or_create_user_model(user_id)
        
        # Filtra interações com feedback
        interactions_with_feedback = [
            interaction for interaction in user_progress.interactions 
            if interaction.feedback
        ]
        
        if not interactions_with_feedback:
            return 0.0
            
        # Inicializa a perda total
        total_loss = 0.0
        
        # Treina o modelo com cada interação
        for interaction in interactions_with_feedback:
            # Prepara os dados de entrada (consulta do usuário)
            query = interaction.query
            self._update_vocabulary(query)
            input_tensor = self._text_to_vector(query)
            
            # Prepara o alvo (feedback classificado)
            # Converte feedback textual em valor numérico (0-1)
            target_value = self._feedback_to_value(interaction.feedback)
            target_tensor = torch.tensor([target_value], dtype=torch.float32)
            
            # Treina o modelo
            model.optimizer.zero_grad()
            output = model(input_tensor.unsqueeze(0))
            loss = self.criterion(output.squeeze(0), target_tensor)
            loss.backward()
            model.optimizer.step()
            
            total_loss += loss.item()
        
        # Salva o modelo treinado
        torch.save(model.state_dict(), os.path.join(self.model_dir, f"model_{user_id}.pt"))
        
        # Retorna a perda média
        return total_loss / len(interactions_with_feedback) if interactions_with_feedback else 0.0
    
    def _feedback_to_value(self, feedback: str) -> float:
        """
        Converte feedback textual em valor numérico.
        
        Args:
            feedback: Feedback textual do usuário
            
        Returns:
            Valor numérico do feedback (0-1)
        """
        feedback = feedback.lower()
        
        # Feedback positivo
        if any(word in feedback for word in ["positivo", "bom", "útil", "gostei", "relevante"]):
            return 1.0
        # Feedback negativo
        elif any(word in feedback for word in ["negativo", "ruim", "inútil", "não gostei", "irrelevante"]):
            return 0.0
        # Feedback neutro
        else:
            return 0.5
    
    def predict_relevance(self, user_id: str, documents: List[Document]) -> List[Tuple[Document, float]]:
        """
        Prediz a relevância de documentos para um usuário específico.
        
        Args:
            user_id: ID do usuário
            documents: Lista de documentos a serem avaliados
            
        Returns:
            Lista de tuplas (documento, relevância) ordenadas por relevância
        """
        # Obtém o modelo do usuário
        model = self.get_or_create_user_model(user_id)
        
        # Lista para armazenar as relevâncias preditas
        document_relevance = []
        
        # Prediz a relevância para cada documento
        for doc in documents:
            # Prepara o texto do documento
            doc_text = doc.content[:500]  # Limita o tamanho para processamento mais rápido
            
            # Converte para tensor
            input_tensor = self._text_to_vector(doc_text)
            
            # Faz a predição
            with torch.no_grad():
                output = model(input_tensor.unsqueeze(0))
                # Corrigido: Calcula a média dos valores do tensor de saída para obter um valor escalar
                if output.numel() > 1:  # Se o tensor tem mais de um elemento
                    relevance = output.mean().item()  # Calcula a média
                else:
                    relevance = output.item()  # Se for um único valor, usa diretamente
            
            # Adiciona à lista
            document_relevance.append((doc, relevance))
        
        # Ordena por relevância (maior para menor)
        document_relevance.sort(key=lambda x: x[1], reverse=True)
        
        return document_relevance
    
    def update_from_user_interactions(self) -> Dict[str, float]:
        """
        Atualiza os modelos para todos os usuários com interações.
        
        Returns:
            Dicionário com os IDs dos usuários e suas perdas de treinamento
        """
        # Obtém todos os usuários
        all_users = self.user_progress_repository.get_all()
        
        # Inicializa o dicionário de perdas
        loss_by_user = {}
        
        # Treina o modelo para cada usuário
        for user_progress in all_users:
            user_id = user_progress.user_id
            loss = self.train_from_feedback(user_id)
            loss_by_user[user_id] = loss
            
        return loss_by_user 