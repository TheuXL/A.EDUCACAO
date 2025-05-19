from typing import List, Dict, Any, Optional, Set, Tuple
import os
import re
import json
from datetime import datetime

from backend.app.domain.entities.document import Document, DocumentType
from backend.app.domain.interfaces.prompt_service import PromptService
from backend.app.application.services.enhanced_search_service import EnhancedSearchService
from backend.app.domain.interfaces.user_progress_repository import UserProgressRepository
from backend.app.domain.entities.user_progress import UserInteraction

class EnhancedPromptServiceImpl(PromptService):
    """
    Implementação aprimorada do serviço de geração de prompts.
    
    Características:
    - Busca mais precisa com indicação de confiança
    - Respostas baseadas no formato preferido do usuário
    - Melhor tratamento quando não há correspondência exata
    - Personalização com base no nível do usuário
    """
    
    # Dicionário de expansão de termos para enriquecer as consultas
    QUERY_EXPANSION = {
        "html": ["html5", "markup", "web", "tag", "elemento"],
        "css": ["estilo", "stylesheet", "design", "layout", "web"],
        "javascript": ["js", "programação", "web", "frontend", "ecmascript"],
        "python": ["programação", "linguagem", "script", "backend"],
        "java": ["programação", "linguagem", "orientação a objetos", "backend"],
        "dados": ["database", "informação", "armazenamento", "banco de dados"],
        "algoritmo": ["lógica", "programação", "solução", "procedimento"],
        "banco de dados": ["sql", "dados", "armazenamento", "consulta"],
        "inteligência artificial": ["ia", "machine learning", "ml", "aprendizado de máquina"],
        "api": ["rest", "interface", "integração", "web service"]
    }
    
    def __init__(
        self, 
        search_service: EnhancedSearchService,
        user_progress_repository: Optional[UserProgressRepository] = None
    ):
        """
        Inicializa o serviço de prompts aprimorado.
        
        Args:
            search_service: Serviço de busca aprimorado
            user_progress_repository: Repositório para acessar o progresso do usuário
        """
        self.search_service = search_service
        self.user_progress_repository = user_progress_repository
        self.session_context = {}  # Armazena o contexto das sessões dos usuários
        
    def generate_response(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        preferred_format: str = "texto",
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Gera uma resposta adaptativa baseada na consulta e perfil do usuário.
        Mantém o contexto da conversa para permitir um diálogo mais fluido.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            user_id: ID do usuário (opcional)
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            Resposta gerada
        """
        try:
            if not conversation_history:
                conversation_history = []
            
            conversation_history.append({"role": "user", "content": query})
            
            search_results = self.search_service.search(query, limit=5)
            
            if not search_results:
                response = self._generate_approximate_response(query, user_level, conversation_history)
                conversation_history.append({"role": "assistant", "content": response})
                
                if user_id:
                    self._store_user_interaction(user_id, query, response)
                
                return response
            
            contexts = []
            for result in search_results:
                contexts.append(f"[{self._get_document_type_name(result.doc_type)}]: {result.content[:500]}...")
            
            conversation_context = ""
            if len(conversation_history) > 1:
                for i, message in enumerate(conversation_history[:-1]):
                    role = "Usuário" if message["role"] == "user" else "Assistente"
                    conversation_context += f"{role}: {message['content']}\n"
            
            level_prompts = {
                "iniciante": "Explique de forma simples e detalhada, evitando termos técnicos complexos",
                "intermediário": "Explique com um equilíbrio entre conceitos básicos e avançados",
                "avançado": "Explique com profundidade técnica, usando terminologia específica da área"
            }
            
            format_indicators = {
                "texto": "📝",
                "vídeo": "📺",
                "imagem": "🖼️",
                "áudio": "🔊"
            }
            
            level_prompt = level_prompts.get(user_level, level_prompts["intermediário"])
            format_indicator = format_indicators.get(preferred_format, "📝")
            
            prompt = f"""
            {conversation_context}
            
            Baseado nos seguintes contextos:
            {' '.join(contexts)}
            
            {level_prompt} a questão do usuário: "{query}"
            
            Considere o nível de conhecimento do usuário ({user_level}) e o formato preferido ({preferred_format}).
            
            Inclua indicações de lacunas de conhecimento se identificar alguma na pergunta.
            Mantenha um tom conversacional e tente identificar subtópicos que o usuário pode se interessar.
            Indique com {format_indicator} no início da resposta.
            """
            
            response = self._process_prompt(prompt, user_level)
            
            if user_id:
                gaps = self._identify_potential_gaps(query, response, user_level)
                if gaps:
                    response += "\n\n💡 Você parece interessado neste tópico. Gostaria de aprofundar seu conhecimento em algum destes aspectos relacionados?\n"
                    for gap in gaps[:3]:
                        response += f"- {gap}\n"
            
            if user_id:
                self._store_user_interaction(user_id, query, response)
                
            conversation_history.append({"role": "assistant", "content": response})
            
            return response
        
        except Exception as e:
            print(f"Erro ao gerar resposta: {str(e)}")
            return "Desculpe, tive um problema ao processar sua consulta. Poderia reformulá-la?"
    
    def _generate_not_found_response(self, query: str, user_level: str) -> str:
        """
        Gera uma resposta quando não são encontrados documentos relevantes.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Resposta formatada para o caso de não haver resultados
        """
        return (
            f"Não sei responder exatamente sua pergunta, mas aqui está uma provável resposta com base nos recursos disponíveis:\n\n"
            f"Infelizmente, não encontrei informações específicas sobre este tópico nos recursos disponíveis. Tente outra pergunta."
        )
    
    def _format_approximate_response(
        self, 
        query: str, 
        excerpts: List[Tuple[Document, str]],
        user_level: str,
        preferred_format: str
    ) -> str:
        """
        Formata uma resposta aproximada quando não há correspondência exata.
        
        Args:
            query: Consulta do usuário
            excerpts: Lista de trechos relevantes
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            
        Returns:
            Resposta aproximada formatada
        """
        if not excerpts:
            return self._generate_not_found_response(query, user_level)
            
        # Extrai tópicos da consulta
        topics = self._extract_topics(query)
        topic_str = ", ".join(topics[:3]) if topics else query
        
        # Cabeçalho da resposta
        response = [
            f"Não sei responder exatamente sua pergunta sobre '{topic_str}', mas aqui está uma resposta baseada nos recursos disponíveis:"
        ]
        
        # Adiciona divisor
        response.append("\n---\n")
        
        # Adiciona o conteúdo mais relevante (primeiro trecho)
        doc, excerpt = excerpts[0]
        
        # Variável para armazenar o caminho do arquivo (se disponível)
        file_path = None
        
        # Formata o conteúdo com base no formato preferido
        if preferred_format == "vídeo" and doc.doc_type == DocumentType.VIDEO:
            timestamp_info = ""
            if doc.metadata and "timestamps" in doc.metadata and doc.metadata["timestamps"]:
                first_segment = doc.metadata["timestamps"][0]
                start_time = first_segment.get("start", 0)
                timestamp_info = f" (Início em {self._format_timestamp(start_time)})"
                
            response.append(f"📺 **Conteúdo em vídeo{timestamp_info}**")
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path:
                file_path = source_path
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
        elif preferred_format == "imagem" and doc.doc_type == DocumentType.IMAGE:
            response.append(f"🖼️ **Conteúdo em imagem**")
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path:
                file_path = source_path
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
        elif preferred_format == "áudio" and doc.doc_type == DocumentType.AUDIO:
            timestamp_info = ""
            if doc.metadata and "timestamps" in doc.metadata and doc.metadata["timestamps"]:
                first_segment = doc.metadata["timestamps"][0]
                start_time = first_segment.get("start", 0)
                timestamp_info = f" (Início em {self._format_timestamp(start_time)})"
                
            response.append(f"🔊 **Conteúdo em áudio{timestamp_info}**")
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path:
                file_path = source_path
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
        elif doc.doc_type == DocumentType.TEXT or doc.doc_type == DocumentType.PDF:
            # Para documentos de texto, verificamos se existe um arquivo markdown
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path and source_path.lower().endswith(('.txt', '.md')):
                file_path = source_path
                response.append(f"📄 **Conteúdo em texto**")
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
        # Adiciona o trecho do conteúdo
        response.append("\n" + excerpt.strip())
        
        # Adiciona a fonte da informação
        if doc.metadata and "title" in doc.metadata:
            response.append(f"\nFonte: {doc.metadata['title']}")
            
        # Adiciona sugestões de tópicos relacionados
        related_topics = self._suggest_related_topics(query)
        if related_topics:
            response.append("\n\nTópicos relacionados que você pode explorar:")
            for topic in related_topics[:3]:
                response.append(f"- {topic}")
        
        # Se temos um caminho de arquivo, adicionamos ao final da resposta em um formato que o frontend possa extrair
        if file_path:
            response.append(f"\n\n<!-- file_path: {file_path} -->")
                
        return "\n".join(response)
    
    def _format_response(
        self, 
        query: str, 
        excerpts: List[Tuple[Document, str]],
        user_level: str,
        preferred_format: str,
        is_exact_match: bool = False
    ) -> str:
        """
        Formata uma resposta com base nos trechos selecionados.
        
        Args:
            query: Consulta do usuário
            excerpts: Lista de trechos relevantes
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            is_exact_match: Indica se é uma correspondência exata
            
        Returns:
            Resposta formatada
        """
        if not excerpts:
            return self._generate_not_found_response(query, user_level)
            
        # Extrai tópicos da consulta
        topics = self._extract_topics(query)
        
        # Variações para introduções de resposta para evitar repetição
        intro_variations = [
            f"Sobre '{', '.join(topics[:2]) if topics else query}':",
            f"Aqui está o que encontrei sobre '{', '.join(topics[:2]) if topics else query}':",
            f"Em relação a '{', '.join(topics[:2]) if topics else query}':",
            f"Respondendo sua pergunta sobre '{', '.join(topics[:2]) if topics else query}':",
            f"Sobre o tema '{', '.join(topics[:2]) if topics else query}':"
        ]
        
        # Cabeçalho da resposta
        response = []
        
        # Não adiciona prefixo para correspondências exatas
        if not is_exact_match:
            import random
            response.append(random.choice(intro_variations))
            response.append("")
        
        # Determina o formato da resposta com base nas preferências e nos documentos disponíveis
        doc, excerpt = excerpts[0]  # Pega o primeiro e mais relevante trecho
        
        # Variável para armazenar o caminho do arquivo (se disponível)
        file_path = None
        
        # Formata o conteúdo com base no formato preferido
        if preferred_format == "vídeo" and doc.doc_type == DocumentType.VIDEO:
            response.append(f"📺 **Conteúdo em vídeo**")
            
            if doc.metadata and "timestamps" in doc.metadata and doc.metadata["timestamps"]:
                first_segment = doc.metadata["timestamps"][0]
                start_time = first_segment.get("start", 0)
                response.append(f"Tempo de início: {self._format_timestamp(start_time)}")
            
            # Extrai o caminho completo do arquivo de vídeo
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path:
                file_path = source_path
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
            # Adiciona uma breve descrição do conteúdo do vídeo
            response.append("\nEste vídeo apresenta:")
            
        elif preferred_format == "imagem" and doc.doc_type == DocumentType.IMAGE:
            response.append(f"🖼️ **Conteúdo em imagem**")
            
            if doc.metadata:
                width = doc.metadata.get("image_width", 0)
                height = doc.metadata.get("image_height", 0)
                if width and height:
                    response.append(f"Dimensões: {width}x{height}")
            
            # Extrai o caminho completo do arquivo de imagem
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path:
                file_path = source_path
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
            # Adiciona uma breve descrição do conteúdo da imagem
            response.append("\nEsta imagem ilustra:")
            
        elif preferred_format == "áudio" and doc.doc_type == DocumentType.AUDIO:
            response.append(f"🔊 **Conteúdo em áudio**")
            
            if doc.metadata and "timestamps" in doc.metadata and doc.metadata["timestamps"]:
                first_segment = doc.metadata["timestamps"][0]
                start_time = first_segment.get("start", 0)
                response.append(f"Tempo de início: {self._format_timestamp(start_time)}")
                
            if doc.metadata and "duration_seconds" in doc.metadata:
                duration = doc.metadata["duration_seconds"]
                response.append(f"Duração: {self._format_timestamp(duration)}")
            
            # Extrai o caminho completo do arquivo de áudio
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path:
                file_path = source_path
                response.append(f"Arquivo: {os.path.basename(source_path)}")
            
            # Adiciona uma breve descrição do conteúdo do áudio
            response.append("\nNeste áudio você ouvirá:")
        
        elif doc.doc_type == DocumentType.TEXT or doc.doc_type == DocumentType.PDF:
            # Para documentos de texto, verificamos se existe um arquivo markdown
            source_path = doc.metadata.get('source', '') if doc.metadata else ''
            if source_path and source_path.lower().endswith(('.txt', '.md')):
                file_path = source_path
                response.append(f"📄 **Conteúdo em texto**")
                response.append(f"Fonte: {os.path.basename(source_path)}")
                response.append("")
        
        # Adiciona o conteúdo principal do trecho
        # Formata o texto para melhor legibilidade
        formatted_excerpt = self._format_content_by_user_level(excerpt.strip(), user_level)
        response.append("\n" + formatted_excerpt)
        
        # Adiciona informações adicionais de outros documentos relevantes
        if len(excerpts) > 1:
            # Variações para introduções de conteúdo complementar
            complement_variations = [
                "\n\n📌 **Informações complementares:**",
                "\n\n🔍 **Saiba mais:**",
                "\n\n📚 **Conteúdo adicional:**",
                "\n\n💡 **Para complementar:**"
            ]
            
            import random
            response.append(random.choice(complement_variations))
            
            for i, (doc, excerpt) in enumerate(excerpts[1:3]):  # Limita a 2 informações adicionais
                # Formata o texto complementar de acordo com o nível do usuário
                formatted_complement = self._format_content_by_user_level(excerpt.strip(), user_level, is_complement=True)
                response.append(f"\n{formatted_complement}")
                
                if doc.metadata and "title" in doc.metadata:
                    response.append(f"Fonte: {doc.metadata['title']}")
                else:
                    source_path = doc.metadata.get('source', '') if doc.metadata else ''
                    if source_path:
                        response.append(f"Fonte: {os.path.basename(source_path)}")
        
        # Adiciona sugestões de tópicos relacionados
        related_topics = self._suggest_related_topics(query)
        if related_topics:
            # Variações para introduções de tópicos relacionados
            related_variations = [
                "\n\n🧐 **Tópicos relacionados:**",
                "\n\n🔗 **Você também pode se interessar por:**",
                "\n\n📋 **Temas relacionados:**",
                "\n\n🌟 **Para expandir seu conhecimento:**"
            ]
            
            import random
            response.append(random.choice(related_variations))
            
            for topic in related_topics[:3]:
                response.append(f"- {topic}")
        
        # Se temos um caminho de arquivo, adicionamos ao final da resposta em um formato que o frontend possa extrair
        if file_path:
            response.append(f"\n\n<!-- file_path: {file_path} -->")
                
        return "\n".join(response)
    
    def _format_content_by_user_level(self, content: str, user_level: str, is_complement: bool = False) -> str:
        """
        Formata o conteúdo de acordo com o nível do usuário.
        
        Args:
            content: Conteúdo a ser formatado
            user_level: Nível de conhecimento do usuário
            is_complement: Se é um conteúdo complementar
            
        Returns:
            Conteúdo formatado
        """
        # Limita o tamanho do conteúdo com base no nível do usuário e se é complementar
        max_length = {
            "iniciante": 300 if not is_complement else 150,
            "intermediário": 500 if not is_complement else 200,
            "avançado": 800 if not is_complement else 300
        }.get(user_level, 500)
        
        # Limita o tamanho do conteúdo
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        # Para iniciantes, destaca termos importantes em negrito
        if user_level == "iniciante":
            # Identifica e destaca termos técnicos
            html_terms = ["HTML", "HTML5", "tag", "elemento", "marcação", "DOCTYPE", "semântica"]
            for term in html_terms:
                if term.lower() in content.lower():
                    # Substitui o termo por sua versão em negrito, preservando maiúsculas/minúsculas
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    content = pattern.sub(lambda m: f"**{m.group(0)}**", content)
        
        return content
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Formata um timestamp em segundos para o formato MM:SS.
        
        Args:
            seconds: Tempo em segundos
            
        Returns:
            String formatada no formato MM:SS
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _expand_query(self, query: str) -> str:
        """
        Expande a consulta com termos relacionados para melhorar a busca.
        
        Args:
            query: Consulta original do usuário
            
        Returns:
            Consulta expandida
        """
        # Tokenização simples
        query_lower = query.lower()
        
        # Verifica se algum termo da consulta está no dicionário de expansão
        for term, expansions in self.QUERY_EXPANSION.items():
            if term.lower() in query_lower:
                # Adiciona até 2 termos de expansão à consulta original
                for expansion in expansions[:2]:
                    if expansion.lower() not in query_lower:
                        query += f" {expansion}"
                break
                
        return query
    
    def _extract_topics(self, query: str) -> List[str]:
        """
        Extrai os principais tópicos de uma consulta.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Lista de tópicos extraídos
        """
        # Tokeniza a consulta
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Lista de palavras irrelevantes (stopwords) em português
        stop_words = {
            "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", 
            "das", "no", "na", "nos", "nas", "ao", "aos", "à", "às", "pelo", "pela", 
            "pelos", "pelas", "em", "por", "para", "com", "sem", "sob", "sobre", 
            "entre", "que", "quem", "qual", "quando", "onde", "como", "porque",
            "e", "ou", "mas", "porém", "entretanto", "contudo", "todavia", "se", 
            "caso", "pois", "logo", "assim", "portanto", "então", "por isso",
            "isto", "isso", "aquilo", "este", "esta", "meu", "minha", "seu", "sua"
        }
        
        # Filtra palavras irrelevantes e curtas
        topics = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Retorna os tópicos únicos
        return list(dict.fromkeys(topics))
    
    def _suggest_related_topics(self, query: str) -> List[str]:
        """
        Sugere tópicos relacionados com base na consulta.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Lista de tópicos relacionados
        """
        topics = self._extract_topics(query)
        
        # Mapeamento simples de tópicos para sugestões relacionadas
        related_topics_map = {
            "html": ["CSS", "JavaScript", "DOM", "HTML5", "Tags semânticas"],
            "css": ["HTML", "Design responsivo", "Flexbox", "Grid layout", "Seletores CSS"],
            "javascript": ["HTML", "CSS", "React", "Node.js", "APIs web"],
            "python": ["Django", "Flask", "Pandas", "NumPy", "APIs REST em Python"],
            "java": ["Spring Boot", "POO", "JVM", "Android", "APIs REST em Java"],
            "aprendizado": ["Técnicas de estudo", "Mapas mentais", "Estilos de aprendizagem"],
            "educação": ["Metodologias ativas", "Ensino híbrido", "Aprendizagem adaptativa"],
            "video": ["Edição de vídeos", "Compressão de mídia", "Formatos de vídeo"]
        }
        
        # Coleta sugestões para os tópicos identificados
        suggestions = []
        for topic in topics:
            if topic in related_topics_map:
                suggestions.extend(related_topics_map[topic])
        
        # Retorna sugestões únicas, até 5
        return list(dict.fromkeys(suggestions))[:5]
    
    def suggest_related_content(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Sugere conteúdos relacionados à consulta do usuário.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            limit: Número máximo de sugestões
            
        Returns:
            Lista de dicionários com informações sobre os conteúdos relacionados
        """
        # Expande a consulta para melhorar os resultados
        expanded_query = self._expand_query(query)
        
        # Busca documentos relacionados
        related_docs, _ = self.search_service.search_by_format_preference(
            query=expanded_query,
            limit=limit+2  # Busca alguns a mais para ter variedade
        )
        
        if not related_docs and query != expanded_query:
            # Tenta com a consulta original
            related_docs, _ = self.search_service.search_by_format_preference(
                query=query,
                limit=limit+2
            )
            
        if not related_docs:
            return []
            
        # Converte os documentos em conteúdos relacionados
        related_content = []
        seen_titles = set()  # Para evitar conteúdos duplicados
        
        for doc in related_docs:
            # Extrai o título do documento
            title = self._extract_title(doc)
            
            # Evita duplicações
            if title in seen_titles:
                continue
                
            seen_titles.add(title)
            
            # Cria o item de conteúdo relacionado
            content_item = {
                "id": doc.id,
                "title": title,
                "type": doc.doc_type.value,
                "preview": self._extract_preview(doc.content),
                "source": self._extract_source(doc)
            }
            
            related_content.append(content_item)
            
            # Limita ao número solicitado
            if len(related_content) >= limit:
                break
                
        return related_content
    
    def _extract_title(self, document: Document) -> str:
        """
        Extrai um título representativo para o documento.
        
        Args:
            document: Documento
            
        Returns:
            Título do documento
        """
        # Se houver um título nos metadados, usa-o
        if document.metadata and "title" in document.metadata:
            return document.metadata["title"]
            
        # Caso contrário, tenta extrair um título do conteúdo
        # Para textos, usa a primeira linha não vazia
        first_line = document.content.strip().split('\n')[0].strip()
        if first_line and len(first_line) < 100:  # Limita o tamanho do título
            return first_line
            
        # Se não conseguir extrair um título, usa o ID do documento
        return f"Documento {document.id}"
    
    def _extract_preview(self, content: str, max_length: int = 100) -> str:
        """
        Extrai uma prévia do conteúdo.
        
        Args:
            content: Conteúdo completo
            max_length: Tamanho máximo da prévia
            
        Returns:
            Prévia do conteúdo
        """
        # Remove quebras de linha extras e espaços
        clean_content = re.sub(r'\s+', ' ', content.strip())
        
        # Limita o tamanho e adiciona reticências se necessário
        if len(clean_content) > max_length:
            return clean_content[:max_length-3] + "..."
            
        return clean_content
    
    def _extract_source(self, document: Document) -> str:
        """
        Extrai a fonte do documento.
        
        Args:
            document: Documento
            
        Returns:
            Fonte do documento
        """
        if document.metadata and "source" in document.metadata:
            return document.metadata["source"]
            
        return document.id
    
    def _select_relevant_excerpts(
        self, 
        documents: List[Document],
        query: str,
        user_level: str,
        preferred_format: str
    ) -> List[Tuple[Document, str]]:
        """
        Seleciona trechos relevantes dos documentos encontrados.
        
        Args:
            documents: Lista de documentos
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido do usuário
            
        Returns:
            Lista de tuplas (documento, trecho_relevante)
        """
        # Extrai as palavras-chave da consulta
        keywords = self._extract_topics(query)
        keyword_set = set(keywords)
        
        # Define o tamanho do trecho com base no nível do usuário
        excerpt_size = self._get_excerpt_size(user_level)
        
        # Lista para armazenar os trechos selecionados
        excerpts = []
        
        # Seleciona trechos de cada documento
        for doc in documents:
            # Verifica se o documento corresponde ao formato preferido
            format_match = self._matches_preferred_format(doc, preferred_format)
            
            # Extrai um trecho relevante
            excerpt = self._extract_relevant_excerpt(
                content=doc.content,
                keywords=keyword_set,
                max_length=excerpt_size
            )
            
            # Adiciona à lista de trechos, priorizando documentos do formato preferido
            if format_match:
                # Insere no início da lista
                excerpts.insert(0, (doc, excerpt))
            else:
                # Adiciona ao final da lista
                excerpts.append((doc, excerpt))
                
        # Reduz a lista para evitar redundância (mantém no máximo 3 trechos)
        result = []
        seen_content = set()
        
        for doc, excerpt in excerpts:
            # Cria uma representação simplificada do conteúdo para verificar duplicações
            content_hash = excerpt[:100]
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                result.append((doc, excerpt))
                
                # Limita a 3 trechos
                if len(result) >= 3:
                    break
                    
        return result
    
    def _matches_preferred_format(self, document: Document, preferred_format: str) -> bool:
        """
        Verifica se o documento corresponde ao formato preferido.
        
        Args:
            document: Documento
            preferred_format: Formato preferido
            
        Returns:
            True se corresponder, False caso contrário
        """
        # Mapeamento de formatos
        format_mapping = {
            "texto": [DocumentType.TEXT, DocumentType.PDF],
            "vídeo": [DocumentType.VIDEO],
            "imagem": [DocumentType.IMAGE],
            "áudio": [DocumentType.AUDIO]
        }
        
        # Verifica se o formato está no mapeamento
        if preferred_format in format_mapping:
            return document.doc_type in format_mapping[preferred_format]
        
        return False
    
    def _get_excerpt_size(self, user_level: str) -> int:
        """
        Define o tamanho do trecho com base no nível do usuário.
        
        Args:
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Tamanho do trecho em caracteres
        """
        if user_level == "iniciante":
            return 250  # Trechos curtos para iniciantes
        elif user_level == "intermediário":
            return 500  # Trechos médios para nível intermediário
        else:  # avançado
            return 750  # Trechos maiores para usuários avançados
    
    def _extract_relevant_excerpt(
        self, 
        content: str, 
        keywords: Set[str],
        max_length: int
    ) -> str:
        """
        Extrai um trecho relevante do conteúdo.
        
        Args:
            content: Conteúdo do documento
            keywords: Palavras-chave da consulta
            max_length: Tamanho máximo do trecho
            
        Returns:
            Trecho relevante
        """
        # Se o conteúdo for pequeno, retorna completo
        if len(content) <= max_length:
            return content
        
        # Divide o conteúdo em parágrafos
        paragraphs = content.split('\n\n')
        
        # Se houver apenas um parágrafo, retorna os primeiros caracteres
        if len(paragraphs) <= 1:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # Calcula a relevância de cada parágrafo
        paragraph_scores = []
        for p in paragraphs:
            score = 0
            p_lower = p.lower()
            for keyword in keywords:
                if keyword.lower() in p_lower:
                    score += 1
            paragraph_scores.append((p, score))
        
        # Ordena os parágrafos por relevância
        paragraph_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Seleciona os parágrafos mais relevantes
        selected_paragraphs = []
        current_length = 0
        
        for p, _ in paragraph_scores:
            # Se adicionar o parágrafo ultrapassar o tamanho máximo, para
            if current_length + len(p) > max_length:
                # Se não temos nenhum parágrafo ainda, pega um trecho do primeiro
                if not selected_paragraphs:
                    return paragraph_scores[0][0][:max_length] + "..."
                break
                
            selected_paragraphs.append(p)
            current_length += len(p) + 2  # +2 para "\n\n"
            
        # Junta os parágrafos selecionados
        return "\n\n".join(selected_paragraphs)
    
    def store_user_interaction(
        self, 
        user_id: str, 
        query: str, 
        response: str, 
        feedback: Optional[str] = None
    ) -> bool:
        """
        Armazena a interação do usuário para uso futuro.
        
        Args:
            user_id: ID do usuário
            query: Consulta do usuário
            response: Resposta fornecida
            feedback: Feedback opcional do usuário
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        if not self.user_progress_repository:
            return False
            
        # Cria um novo objeto de interação
        interaction = UserInteraction(
            query=query,
            response=response,
            feedback=feedback,
            timestamp=datetime.now()
        )
        
        # Armazena no repositório
        return self.user_progress_repository.update_interaction(
            user_id=user_id,
            query=query,
            response=response,
            feedback=feedback
        )
    
    def _identify_potential_gaps(self, query: str, response: str, user_level: str) -> List[str]:
        """
        Identifica possíveis lacunas de conhecimento baseadas na consulta e resposta.
        
        Args:
            query: Consulta do usuário
            response: Resposta gerada
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Lista de possíveis tópicos para explorar
        """
        # Extrair palavras-chave da consulta
        query_keywords = set(query.lower().split())
        
        # Algumas palavras-chave comuns que indicam incerteza ou lacunas
        uncertainty_indicators = {"como", "porque", "por que", "o que é", "definição", "explique", 
                                 "diferença", "funcionamento", "dúvida", "não entendo"}
        
        # Verifica se há indicadores de incerteza na consulta
        has_uncertainty = any(indicator in query.lower() for indicator in uncertainty_indicators)
        
        # Sugestões baseadas no nível do usuário
        if user_level == "iniciante":
            if has_uncertainty:
                return [
                    "Conceitos fundamentais relacionados a este tópico",
                    "Exemplos práticos e aplicações do dia a dia",
                    "Materiais introdutórios em formato visual"
                ]
            else:
                return [
                    "Princípios básicos para aprofundar seu conhecimento",
                    "Etapas iniciais para aplicar este conhecimento",
                    "Recursos recomendados para iniciantes"
                ]
        elif user_level == "intermediário":
            return [
                "Estudos de caso e aplicações práticas",
                "Técnicas avançadas relacionadas a este tópico",
                "Desafios comuns e como superá-los"
            ]
        else:  # avançado
            return [
                "Pesquisas recentes e desenvolvimentos nesta área",
                "Aplicações complexas e casos de uso específicos",
                "Tópicos avançados para exploração adicional"
            ] 
    
    def _get_document_type_name(self, doc_type: DocumentType) -> str:
        """
        Retorna o nome amigável do tipo de documento.
        
        Args:
            doc_type: Tipo de documento
            
        Returns:
            Nome amigável do tipo
        """
        type_names = {
            DocumentType.TEXT: "Texto",
            DocumentType.PDF: "Pdf",
            DocumentType.VIDEO: "Vídeo",
            DocumentType.IMAGE: "Imagem",
            DocumentType.JSON: "Json",
            DocumentType.AUDIO: "Áudio"
        }
        
        return type_names.get(doc_type, "Desconhecido")

    def _generate_approximate_response(self, query: str, user_level: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Gera uma resposta aproximada quando não há resultados de busca.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            conversation_history: Histórico da conversa
            
        Returns:
            Resposta aproximada
        """
        # Tenta uma busca mais ampla com termos expandidos
        expanded_query = self._expand_query(query)
        search_results = self.search_service.search(expanded_query, limit=5)
        
        if search_results:
            # Se encontrou resultados com a busca expandida, seleciona trechos relevantes
            excerpts = self._select_relevant_excerpts(
                search_results,
                query,
                user_level,
                "texto"  # Usa texto como formato padrão para respostas aproximadas
            )
            
            # Formata a resposta usando a função de formatação regular
            # mas indicando que é uma resposta aproximada
            return self._format_response(query, excerpts, user_level, "texto", is_exact_match=False)
        else:
            # Tenta buscar por tópicos relacionados ao HTML5 ou desenvolvimento web
            fallback_topics = [
                "HTML5 básico",
                "estrutura de página web",
                "tags HTML",
                "desenvolvimento web",
                "elementos HTML"
            ]
            
            # Tenta cada tópico até encontrar algo relevante
            for topic in fallback_topics:
                fallback_results = self.search_service.search(topic, limit=3)
                if fallback_results:
                    # Encontrou algo com um tópico de fallback
                    excerpts = self._select_relevant_excerpts(
                        fallback_results,
                        query,
                        user_level,
                        "texto"
                    )
                    
                    # Prepara uma resposta que indica que é uma sugestão alternativa
                    response = [
                        f"Não encontrei informações específicas sobre '{query}', mas aqui está algo relacionado que pode ajudar:",
                        ""
                    ]
                    
                    # Adiciona o conteúdo mais relevante
                    doc, excerpt = excerpts[0]
                    
                    # Formata o conteúdo para o nível do usuário
                    formatted_excerpt = self._format_content_by_user_level(excerpt.strip(), user_level)
                    response.append(formatted_excerpt)
                    
                    # Adiciona a fonte
                    if doc.metadata and "title" in doc.metadata:
                        response.append(f"\nFonte: {doc.metadata['title']}")
                    elif doc.metadata and "source" in doc.metadata:
                        response.append(f"\nFonte: {os.path.basename(doc.metadata['source'])}")
                    
                    # Sugere reformular a pergunta
                    response.append("\n\n💡 Talvez você queira reformular sua pergunta ou explorar alguns destes tópicos relacionados:")
                    
                    # Adiciona sugestões de tópicos relacionados ao HTML5
                    html_topics = ["estrutura básica de HTML5", "tags semânticas", "formatação de texto em HTML", "listas e tabelas em HTML"]
                    for html_topic in html_topics[:3]:
                        response.append(f"- {html_topic}")
                    
                    return "\n".join(response)
            
            # Se não encontrou nada com os tópicos de fallback, retorna uma resposta genérica
            return self._generate_creative_not_found_response(query, user_level)
    
    def _generate_creative_not_found_response(self, query: str, user_level: str) -> str:
        """
        Gera uma resposta criativa quando não há resultados disponíveis.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Resposta criativa
        """
        # Extrai palavras-chave da consulta
        keywords = self._extract_topics(query)
        
        # Diferentes formatos de resposta para evitar repetição
        responses = [
            f"Não encontrei informações específicas sobre '{query}' nos recursos disponíveis. Que tal explorar um destes tópicos relacionados ao HTML5?",
            f"Ainda não tenho conteúdo específico sobre '{query}', mas posso ajudar com estes tópicos fundamentais de HTML5:",
            f"Sua pergunta sobre '{query}' é interessante, mas não encontrei recursos diretos. Considere explorar estes tópicos relacionados:"
        ]
        
        import random
        response = [random.choice(responses), ""]
        
        # Adiciona tópicos fundamentais de HTML5 como sugestões
        fundamental_topics = [
            "Estrutura básica de uma página HTML5",
            "Tags semânticas como header, footer, nav e article",
            "Formatação de texto com HTML5",
            "Criação de listas e tabelas em HTML5",
            "Links e âncoras em documentos HTML"
        ]
        
        # Adiciona 3-4 tópicos aleatórios
        selected_topics = random.sample(fundamental_topics, min(4, len(fundamental_topics)))
        for topic in selected_topics:
            response.append(f"- {topic}")
        
        # Adiciona uma sugestão para reformular a pergunta
        response.append("\nTente reformular sua pergunta ou escolha um dos tópicos acima para aprender mais.")
        
        return "\n".join(response) 