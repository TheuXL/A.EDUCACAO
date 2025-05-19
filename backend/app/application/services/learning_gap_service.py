from typing import List, Dict, Any, Optional, Set, Tuple
import re
from collections import Counter
from datetime import datetime, timedelta

from backend.app.domain.interfaces.learning_gap_analyzer import LearningGapAnalyzer
from backend.app.domain.interfaces.user_progress_repository import UserProgressRepository
from backend.app.domain.interfaces.search_service import SearchService
from backend.app.domain.entities.user_progress import UserProgress, UserInteraction


class LearningGapServiceImpl(LearningGapAnalyzer):
    """
    Implementação do serviço de análise de lacunas de aprendizado.
    
    Este serviço analisa as interações do usuário para identificar lacunas de conhecimento com base no histórico de interações do usuário, analisando padrões de consultas, feedback negativo e tempo gasto em determinados tópicos.
    """
    
    # Limiar para considerar um tópico como sendo uma lacuna de conhecimento
    GAP_THRESHOLD = 0.6  # 60% de consultas/feedback negativo sobre um tópico
    
    # Categorias de tópicos para agrupamento
    TOPIC_CATEGORIES = {
        "programação": ["python", "java", "javascript", "código", "algoritmo", "função", "variável"],
        "web": ["html", "css", "frontend", "backend", "api", "http", "rest"],
        "dados": ["banco", "database", "sql", "análise", "data", "json", "tabela"],
        "educacional": ["aprendizado", "estudo", "conceito", "teoria", "prática", "exercício"],
        "matemática": ["álgebra", "geometria", "cálculo", "estatística", "probabilidade"]
    }
    
    def __init__(
        self, 
        user_repository: UserProgressRepository,
        search_service: Optional[SearchService] = None
    ):
        """
        Inicializa o serviço de análise de lacunas.
        
        Args:
            user_repository: Repositório para acesso ao progresso do usuário
            search_service: Serviço de busca para encontrar conteúdo relacionado (opcional)
        """
        self.user_repository = user_repository
        self.search_service = search_service
    
    def analyze_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Analisa o progresso do usuário para identificar padrões e lacunas.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com análise detalhada do progresso, incluindo lacunas identificadas
        """
        user_progress = self.user_repository.get_by_id(user_id)
        
        if not user_progress or not user_progress.interactions:
            return {
                "user_id": user_id,
                "status": "insufficient_data",
                "message": "Dados insuficientes para análise de lacunas",
                "gaps": []
            }
        
        identified_gaps = self.identify_gaps(user_progress)
        engagement_metrics = user_progress.calculate_engagement_metrics()
        progress_score = self._calculate_progress_score(user_progress)
        improvement_suggestions = self._generate_suggestions(identified_gaps, user_progress.profile.level)
        
        return {
            "user_id": user_id,
            "status": "success",
            "analysis_date": datetime.now().isoformat(),
            "overall_progress": progress_score,
            "engagement_metrics": engagement_metrics,
            "identified_gaps": identified_gaps,
            "improvement_suggestions": improvement_suggestions,
            "strengths": user_progress.profile.strengths,
            "weaknesses": user_progress.profile.weaknesses
        }
    
    def identify_gaps(self, user_progress: UserProgress) -> List[Dict[str, Any]]:
        """
        Identifica lacunas específicas no conhecimento do usuário.
        
        Args:
            user_progress: Objeto com o progresso do usuário
            
        Returns:
            Lista de lacunas identificadas com metadados (tópico, nível, sugestões)
        """
        if not user_progress.interactions:
            return []
        
        topic_frequency = self._analyze_topic_frequency(user_progress.interactions)
        negative_feedback_topics = self._analyze_negative_feedback(user_progress.interactions)
        time_per_topic = self._analyze_time_per_topic(user_progress.interactions)
        
        gaps = []
        all_topics = set(topic_frequency.keys()) | set(negative_feedback_topics.keys())
        
        for topic in all_topics:
            gap_score = 0.0
            
            # Fatores da pontuação:
            # 1. Frequência do tópico (ponderado por 0.3)
            freq_score = topic_frequency.get(topic, 0) / max(topic_frequency.values()) if topic_frequency else 0
            gap_score += freq_score * 0.3
            
            # 2. Feedback negativo (ponderado por 0.5)
            neg_score = negative_feedback_topics.get(topic, 0)
            gap_score += neg_score * 0.5
            
            # 3. Tempo por tópico (ponderado por 0.2)
            time_score = time_per_topic.get(topic, 0) / max(time_per_topic.values()) if time_per_topic else 0
            gap_score += time_score * 0.2
            
            if gap_score >= self.GAP_THRESHOLD:
                severity = "alta" if gap_score > 0.8 else "média" if gap_score > 0.7 else "baixa"
                category = self._determine_topic_category(topic)
                
                gaps.append({
                    "topic": topic,
                    "category": category,
                    "score": round(gap_score, 2),
                    "severity": severity,
                    "frequency": topic_frequency.get(topic, 0),
                    "negative_feedback": negative_feedback_topics.get(topic, 0),
                    "time_intensity": time_per_topic.get(topic, 0)
                })
        
        gaps.sort(key=lambda x: (x["severity"] == "alta", x["severity"] == "média", x["score"]), reverse=True)
        
        return gaps
    
    def generate_improvement_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Gera um plano de melhoria para preencher as lacunas identificadas.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Plano de melhoria com passos recomendados e recursos
        """
        # Analisa o progresso para identificar lacunas
        analysis = self.analyze_progress(user_id)
        
        if analysis["status"] != "success" or not analysis["identified_gaps"]:
            return {
                "user_id": user_id,
                "status": "no_gaps_identified",
                "message": "Não foram identificadas lacunas significativas",
                "plan": []
            }
        
        # Obtém o nível do usuário
        user_progress = self.user_repository.get_by_id(user_id)
        user_level = user_progress.profile.level if user_progress else "intermediário"
        
        # Cria passos para cada lacuna identificada
        improvement_steps = []
        
        for i, gap in enumerate(analysis["identified_gaps"][:3], 1):  # Limita aos 3 principais
            topic = gap["topic"]
            category = gap["category"]
            severity = gap["severity"]
            
            # Ajusta o nível para conteúdos recomendados com base na severidade
            content_level = self._adjust_level_for_gap(user_level, severity)
            
            # Busca recursos relacionados se o serviço de busca estiver disponível
            related_resources = []
            if self.search_service:
                try:
                    query = f"aprender {topic} {category} conceitos básicos"
                    results = self.search_service.search(query, limit=3)
                    
                    if results:
                        for doc in results:
                            related_resources.append({
                                "id": doc.id,
                                "title": self._extract_title(doc),
                                "type": doc.doc_type.value,
                                "preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                            })
                except Exception as e:
                    print(f"Erro ao buscar recursos relacionados: {e}")
            
            # Adiciona passo ao plano
            step = {
                "step": i,
                "topic": topic,
                "category": category,
                "goal": f"Preencher lacuna de conhecimento em '{topic}'",
                "suggested_approach": self._generate_approach_for_gap(topic, severity, content_level),
                "resources": related_resources,
                "estimated_time": "1-2 horas" if severity == "baixa" else "3-5 horas" if severity == "média" else "5-10 horas"
            }
            
            improvement_steps.append(step)
        
        # Cria o plano completo
        current_date = datetime.now()
        
        return {
            "user_id": user_id,
            "status": "success",
            "creation_date": current_date.isoformat(),
            "recommended_completion_date": (current_date + timedelta(days=14)).isoformat(),
            "plan_title": "Plano de Melhoria Personalizado",
            "steps": improvement_steps,
            "overall_goal": "Melhorar o entendimento dos tópicos identificados como lacunas de conhecimento"
        }
    
    def update_user_strengths_weaknesses(self, user_id: str) -> bool:
        """
        Atualiza os pontos fortes e fracos no perfil do usuário com base nas análises.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        user_progress = self.user_repository.get_by_id(user_id)
        
        if not user_progress:
            return False
        
        # Identifica lacunas atuais
        gaps = self.identify_gaps(user_progress)
        
        # Extrai tópicos de lacunas como pontos fracos
        weaknesses = [gap["topic"] for gap in gaps if gap["severity"] in ["média", "alta"]]
        
        # Analisa interações para identificar pontos fortes
        strengths = self._identify_strengths(user_progress.interactions)
        
        # Limita o número de pontos fortes e fracos
        weaknesses = weaknesses[:5]  # Máximo 5 pontos fracos
        strengths = strengths[:5]    # Máximo 5 pontos fortes
        
        # Atualiza o perfil do usuário
        user_progress.update_profile(
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        # Salva as alterações no repositório
        return self.user_repository.save(user_progress)
    
    def _analyze_topic_frequency(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """
        Analisa a frequência de tópicos nas interações do usuário.
        
        Args:
            interactions: Lista de interações do usuário
            
        Returns:
            Dicionário com a contagem de ocorrência de cada tópico
        """
        topic_counts = Counter()
        
        for interaction in interactions:
            # Extrai tópicos da consulta
            topics = self._extract_topics(interaction.query)
            
            # Incrementa contagem para cada tópico
            for topic in topics:
                topic_counts[topic] += 1
                
        return dict(topic_counts)
    
    def _analyze_negative_feedback(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """
        Analisa feedback negativo por tópico nas interações.
        
        Args:
            interactions: Lista de interações do usuário
            
        Returns:
            Dicionário com a proporção de feedback negativo por tópico
        """
        # Contagem de tópicos e feedback negativo
        topic_total = Counter()
        topic_negative = Counter()
        
        for interaction in interactions:
            if not interaction.feedback:
                continue
                
            # Extrai tópicos da consulta
            topics = self._extract_topics(interaction.query)
            
            # Analisa o feedback
            is_negative = any(word in interaction.feedback.lower() 
                             for word in ["negativo", "ruim", "difícil", "confuso", "não ajudou", "não entendi"])
            
            # Incrementa contadores
            for topic in topics:
                topic_total[topic] += 1
                if is_negative:
                    topic_negative[topic] += 1
        
        # Calcula proporção de feedback negativo
        negative_ratio = {}
        for topic in topic_total:
            if topic_total[topic] > 0:
                negative_ratio[topic] = topic_negative[topic] / topic_total[topic]
            else:
                negative_ratio[topic] = 0.0
                
        return negative_ratio
    
    def _analyze_time_per_topic(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """
        Analisa o tempo gasto por tópico (estimado pela frequência e intervalos entre interações).
        
        Args:
            interactions: Lista de interações do usuário
            
        Returns:
            Dicionário com o tempo relativo gasto por tópico
        """
        # Ordenar interações por timestamp
        sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)
        
        # Mapeamento de tópicos para tempo acumulado (arbitrário)
        topic_time = Counter()
        
        # Processa interações sequencialmente para estimar tempo
        for i in range(len(sorted_interactions) - 1):
            current = sorted_interactions[i]
            next_int = sorted_interactions[i + 1]
            
            # Tempo entre interações em minutos
            time_diff = (next_int.timestamp - current.timestamp).total_seconds() / 60
            
            # Se o tempo for muito grande (> 30 min), assume desconexão
            if time_diff > 30:
                time_diff = 5  # Assume 5 minutos padrão
            
            # Extrai tópicos da consulta atual
            topics = self._extract_topics(current.query)
            
            # Distribui o tempo entre os tópicos
            if topics:
                time_per_topic = time_diff / len(topics)
                for topic in topics:
                    topic_time[topic] += time_per_topic
        
        # Para a última interação, assume tempo padrão
        if sorted_interactions:
            last_topics = self._extract_topics(sorted_interactions[-1].query)
            for topic in last_topics:
                topic_time[topic] += 5  # Assume 5 minutos padrão
                
        return dict(topic_time)
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extrai tópicos de um texto.
        
        Args:
            text: Texto para extrair tópicos
            
        Returns:
            Lista de tópicos extraídos
        """
        # Remove caracteres especiais e normaliza
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Remove palavras comuns (stop words)
        stop_words = {"como", "qual", "quais", "porque", "por", "que", "e", "o", "a", "os", "as", 
                      "um", "uma", "para", "em", "da", "do", "das", "dos", "me", "meu", "minha", 
                      "seu", "sua", "este", "esta", "isso", "aquilo", "estes", "estas"}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Identifica n-gramas importantes (ex: "banco de dados")
        bigrams = []
        for i in range(len(filtered_words) - 1):
            bigram = filtered_words[i] + " " + filtered_words[i + 1]
            if (
                any(term in bigram for term in self._get_all_category_terms()) or 
                bigram in ["aprendizado máquina", "banco dados", "ciência dados", "inteligência artificial"]
            ):
                bigrams.append(bigram)
        
        # Combina unigrams e bigrams, priorizando bigrams
        topics = bigrams + filtered_words
        
        # Remove duplicações e limita a 5 tópicos
        unique_topics = []
        for topic in topics:
            is_duplicate = False
            for existing in unique_topics:
                if topic in existing or existing in topic:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_topics.append(topic)
        
        return unique_topics[:5]
    
    def _determine_topic_category(self, topic: str) -> str:
        """
        Determina a categoria de um tópico.
        
        Args:
            topic: Tópico para categorizar
            
        Returns:
            Categoria do tópico
        """
        topic_lower = topic.lower()
        
        for category, terms in self.TOPIC_CATEGORIES.items():
            if any(term in topic_lower for term in terms):
                return category
                
        return "geral"
    
    def _get_all_category_terms(self) -> List[str]:
        """
        Retorna todos os termos de todas as categorias.
        
        Returns:
            Lista de todos os termos de categorias
        """
        all_terms = []
        for terms in self.TOPIC_CATEGORIES.values():
            all_terms.extend(terms)
        return all_terms
    
    def _calculate_progress_score(self, user_progress: UserProgress) -> float:
        """
        Calcula uma pontuação de progresso geral do usuário.
        
        Args:
            user_progress: Progresso do usuário
            
        Returns:
            Pontuação de progresso (0.0 a 1.0)
        """
        # Fatores para pontuação:
        # 1. Número de interações (mais interações = mais progresso)
        # 2. Diversidade de tópicos explorados
        # 3. Proporção de feedback positivo
        # 4. Tendência de feedback recente (melhoria ao longo do tempo)
        
        # Se não há interações, retorna zero
        if not user_progress.interactions:
            return 0.0
        
        # Base: número de interações (normalizado até 100)
        interaction_count = len(user_progress.interactions)
        interaction_score = min(1.0, interaction_count / 100)
        
        # Diversidade de tópicos
        all_topics = set()
        for interaction in user_progress.interactions:
            all_topics.update(self._extract_topics(interaction.query))
        
        topic_diversity = min(1.0, len(all_topics) / 20)  # Normaliza até 20 tópicos
        
        # Feedback positivo
        positive_count = 0
        total_with_feedback = 0
        
        for interaction in user_progress.interactions:
            if interaction.feedback:
                total_with_feedback += 1
                if any(word in interaction.feedback.lower() 
                      for word in ["positivo", "bom", "útil", "ajudou", "entendi", "claro"]):
                    positive_count += 1
        
        feedback_score = positive_count / total_with_feedback if total_with_feedback > 0 else 0.5
        
        # Tendência de melhoria
        recent_trend = 0.5  # Neutro por padrão
        if interaction_count >= 5:
            recent_interactions = sorted(user_progress.interactions, key=lambda x: x.timestamp)[-5:]
            recent_positive = 0
            recent_with_feedback = 0
            
            for interaction in recent_interactions:
                if interaction.feedback:
                    recent_with_feedback += 1
                    if any(word in interaction.feedback.lower() 
                          for word in ["positivo", "bom", "útil", "ajudou", "entendi", "claro"]):
                        recent_positive += 1
            
            recent_trend = recent_positive / recent_with_feedback if recent_with_feedback > 0 else 0.5
        
        # Calcula pontuação final (ponderada)
        progress_score = (
            (interaction_score * 0.3) + 
            (topic_diversity * 0.2) + 
            (feedback_score * 0.25) + 
            (recent_trend * 0.25)
        )
        
        return round(progress_score, 2)
    
    def _generate_approach_for_gap(self, topic: str, severity: str, level: str) -> str:
        """
        Gera uma abordagem sugerida para uma lacuna específica.
        
        Args:
            topic: Tópico da lacuna
            severity: Gravidade da lacuna (alta, média, baixa)
            level: Nível de conhecimento ajustado
            
        Returns:
            Abordagem sugerida como texto
        """
        if severity == "alta":
            return (
                f"Revisar conceitos fundamentais de {topic} com materiais de nível {level}. "
                f"Recomenda-se dedicar pelo menos 1 hora diária para este tópico, "
                f"começando com conceitos básicos e exercícios práticos simples."
            )
        elif severity == "média":
            return (
                f"Reforçar o conhecimento de {topic} com exercícios práticos de nível {level}. "
                f"Experimente aplicar os conceitos em pequenos projetos para consolidar "
                f"o aprendizado e identificar pontos específicos de dificuldade."
            )
        else:  # baixa
            return (
                f"Aprofundar conhecimentos em {topic} com recursos avançados de nível {level}. "
                f"Busque aplicar os conceitos em situações desafiadoras e conectar "
                f"com outros tópicos para fortalecer o entendimento."
            )
    
    def _adjust_level_for_gap(self, user_level: str, severity: str) -> str:
        """
        Ajusta o nível de conteúdo recomendado com base na gravidade da lacuna.
        
        Args:
            user_level: Nível atual do usuário
            severity: Gravidade da lacuna
            
        Returns:
            Nível ajustado para recomendações
        """
        if severity == "alta":
            # Reduz um nível para lacunas graves
            return "iniciante" if user_level != "iniciante" else "iniciante"
        elif severity == "média":
            # Mantém o mesmo nível para lacunas médias
            return user_level
        else:
            # Aumenta um nível para lacunas leves (desafio)
            return "avançado" if user_level != "avançado" else "avançado"
    
    def _generate_suggestions(
        self, 
        gaps: List[Dict[str, Any]], 
        user_level: str
    ) -> List[Dict[str, Any]]:
        """
        Gera sugestões de melhoria com base nas lacunas identificadas.
        
        Args:
            gaps: Lista de lacunas identificadas
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Lista de sugestões de melhoria
        """
        suggestions = []
        
        for gap in gaps[:3]:  # Limita às 3 principais lacunas
            topic = gap["topic"]
            severity = gap["severity"]
            category = gap["category"]
            
            # Ajusta o nível com base na severidade
            adjusted_level = self._adjust_level_for_gap(user_level, severity)
            
            suggestion = {
                "topic": topic,
                "title": f"Melhorar conhecimento em {topic}",
                "description": self._generate_approach_for_gap(topic, severity, adjusted_level),
                "category": category,
                "severity": severity,
                "level": adjusted_level
            }
            
            suggestions.append(suggestion)
            
        return suggestions
    
    def _identify_strengths(self, interactions: List[UserInteraction]) -> List[str]:
        """
        Identifica pontos fortes do usuário com base em padrões de interação.
        
        Args:
            interactions: Lista de interações do usuário
            
        Returns:
            Lista de tópicos identificados como pontos fortes
        """
        # Conta feedback positivo por tópico
        topic_total = Counter()
        topic_positive = Counter()
        
        for interaction in interactions:
            if not interaction.feedback:
                continue
                
            # Extrai tópicos da consulta
            topics = self._extract_topics(interaction.query)
            
            # Verifica se é feedback positivo
            is_positive = any(word in interaction.feedback.lower() 
                             for word in ["positivo", "bom", "útil", "ajudou", "entendi", "claro"])
            
            # Incrementa contadores
            for topic in topics:
                topic_total[topic] += 1
                if is_positive:
                    topic_positive[topic] += 1
        
        # Identifica tópicos com alta proporção de feedback positivo
        strengths = []
        for topic, count in topic_total.items():
            if count >= 3:  # Mínimo de 3 interações sobre o tópico
                positive_ratio = topic_positive[topic] / count if count > 0 else 0
                if positive_ratio >= 0.7:  # 70% de feedback positivo
                    strengths.append(topic)
        
        # Ordena por número de feedback positivo
        strengths.sort(key=lambda x: topic_positive[x], reverse=True)
        
        return strengths
    
    def _extract_title(self, doc) -> str:
        """
        Extrai um título representativo do documento.
        
        Args:
            doc: Documento
            
        Returns:
            Título representativo
        """
        if hasattr(doc, 'metadata') and doc.metadata and 'title' in doc.metadata:
            return doc.metadata['title']
        
        # Se não tiver título nos metadados, usa as primeiras palavras do conteúdo
        if hasattr(doc, 'content') and doc.content:
            first_line = doc.content.strip().split('\n')[0]
            if len(first_line) > 50:
                return first_line[:47] + "..."
            return first_line
        
        return f"Recurso {doc.id}" 