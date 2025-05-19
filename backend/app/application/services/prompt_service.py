from typing import List, Dict, Any, Optional, Tuple, Set
import re
from pathlib import Path
from datetime import datetime
import os

from backend.app.domain.entities.document import Document, DocumentType
from backend.app.domain.interfaces.prompt_service import PromptService
from backend.app.domain.interfaces.search_service import SearchService
from backend.app.domain.interfaces.user_progress_repository import UserProgressRepository
from backend.app.domain.entities.user_progress import UserProgress, UserInteraction
from backend.app.infrastructure.repositories.json_user_progress_repository import JsonUserProgressRepository


class PromptServiceImpl(PromptService):
    """
    Implementação do serviço de geração de respostas adaptativas.
    Utiliza o SearchService para encontrar documentos relevantes e gera
    respostas personalizadas com base no perfil do usuário.
    """
    
    # Dicionário de expansão de termos para enriquecer as consultas
    QUERY_EXPANSION = {
          "html5": ["html", "web", "markup", "tags", "estrutura"],
    "estrutura": ["html5", "html", "web", "markup", "semântica"],
    "navegador": ["browser", "chrome", "firefox", "web", "html"],
    "páginas": ["html5", "web", "interface", "documento"],
    "tags": ["html", "html5", "markup", "elemento", "estrutura"],
    "elementos": ["tag", "html", "html5", "web"],
    "lista": ["ordenada", "não ordenada", "html", "markup"],
    "tabela": ["html", "markup", "web", "dados"],
    "link": ["html", "navegação", "url", "web"],
    "figura": ["imagem", "media", "html", "web"],
    "conteúdo": ["informação", "dados", "página", "html"],
    "criação": ["markup", "estrutura", "web"],
    "texto": ["parágrafo", "html", "documento", "markup"]
    }
    
    def __init__(
        self, 
        search_service: SearchService,
        user_progress_repository: Optional[UserProgressRepository] = None
    ):
        """
        Inicializa o serviço de prompt.
        
        Args:
            search_service: Serviço de busca para encontrar documentos relevantes
            user_progress_repository: Repositório para armazenamento do progresso do usuário.
                                     Se None, utiliza JsonUserProgressRepository.
        """
        self.search_service = search_service
        
        # Se não for fornecido um repositório, usa o JsonUserProgressRepository
        if user_progress_repository is None:
            self.user_progress_repository = JsonUserProgressRepository()
        else:
            self.user_progress_repository = user_progress_repository
            
        # Manter contexto da sessão
        self.session_context = {}
        
        # Diretório base
        base_dir = Path(os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", ".."
        )))
        
        # Diretório de recursos processados
        self.resources_dir = base_dir / "processed_data"
        
        # Verifica se há recursos disponíveis
        self.available_resources = self._check_available_resources()
    
    def _check_available_resources(self) -> Dict[str, List[str]]:
        """
        Verifica quais recursos estão disponíveis no diretório de recursos.
        
        Returns:
            Dicionário com os tipos de recursos disponíveis
        """
        resources = {
            "text": [],
            "pdf": [],
            "video": [],
            "image": [],
            "audio": [],
            "json": []
        }
        
        # Diretório base
        base_dir = Path(os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", ".."
        )))
        
        # Diretório de recursos processados
        processed_dir = base_dir / "processed_data"
        
        # Verifica se o diretório de textos processados existe
        text_dir = processed_dir / "text"
        if text_dir.exists():
            for file_path in text_dir.glob("*.txt"):
                resources["text"].append(str(file_path))
        
        # Verifica se o diretório de vídeos processados existe
        videos_dir = processed_dir / "videos"
        if videos_dir.exists():
            for file_path in videos_dir.glob("*"):
                resources["video"].append(str(file_path))
        
        # Verifica se o diretório de imagens processadas existe
        images_dir = processed_dir / "images"
        if images_dir.exists():
            for file_path in images_dir.glob("*"):
                resources["image"].append(str(file_path))
        
        # Verifica se o diretório de áudios processados existe
        audio_dir = processed_dir / "audio"
        if audio_dir.exists():
            for file_path in audio_dir.glob("*"):
                resources["audio"].append(str(file_path))
        
        # Verifica se o diretório de transcrições existe
        transcripts_dir = processed_dir / "transcripts"
        if transcripts_dir.exists():
            for file_path in transcripts_dir.glob("*_ocr.txt"):
                resources["image"].append(str(file_path))
        
        return resources
    
    def generate_response(
        self, 
        query: str, 
        user_level: str = "intermediário", 
        preferred_format: str = "texto",
        user_id: Optional[str] = None
    ) -> str:
        """
        Gera uma resposta adaptativa para a consulta do usuário.
        
        Args:
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário (iniciante, intermediário, avançado)
            preferred_format: Formato preferido de conteúdo (texto, vídeo, imagem)
            user_id: Identificador opcional do usuário para armazenar interações
            
        Returns:
            Resposta adaptativa ao usuário
        """
        # Atualiza o contexto da sessão para o usuário
        if user_id:
            if user_id not in self.session_context:
                self.session_context[user_id] = {"last_query": "", "topics": []}
            
            # Adiciona a consulta atual ao contexto e mantém as últimas 3 consultas
            self.session_context[user_id]["last_query"] = query
            self.session_context[user_id]["topics"] = self._extract_topics(query)
        
        # Expande a consulta com termos relacionados
        expanded_query = self._expand_query(query)
        
        # Busca documentos relacionados à consulta expandida
        related_docs = self.search_service.search(expanded_query, limit=5)
        
        # Se não encontrar com a consulta expandida, tenta com a consulta original
        if not related_docs:
            related_docs = self.search_service.search(query, limit=5)
        
        # Verifica se foram encontrados documentos
        if not related_docs:
            # Tenta buscar em todos os recursos disponíveis
            related_docs = self._search_in_all_resources(query)
            
            if not related_docs:
                # Tenta sugerir tópicos relacionados quando não há resultados
                suggested_topics = self._suggest_related_topics(query)
                
                if suggested_topics:
                    response = (
                        f"Não sei responder exatamente sua pergunta sobre '{query}', mas aqui está uma provável resposta baseada nos recursos disponíveis:\n\n"
                        f"Você pode estar interessado nestes tópicos relacionados:\n"
                    )
                    for i, topic in enumerate(suggested_topics, 1):
                        response += f"  {i}. {topic}\n"
                    response += "\nPor favor, tente reformular sua pergunta ou explorar um destes tópicos."
                else:
                    response = (
                        f"Não sei responder exatamente sua pergunta sobre '{query}', mas aqui está uma provável resposta baseada nos recursos disponíveis:\n\n"
                        f"Por favor, tente reformular sua pergunta para que eu possa encontrar informações relevantes nos recursos disponíveis."
                    )
            else:
                # Se encontrou documentos após busca em todos os recursos, continua o processamento
                response = self._process_found_documents(related_docs, query, user_level, preferred_format)
        else:
            # Processa os documentos encontrados
            response = self._process_found_documents(related_docs, query, user_level, preferred_format)
        
        # Armazena a interação do usuário, se possível
        if user_id and self.user_progress_repository:
            self.store_user_interaction(
                user_id=user_id,
                query=query,
                response=response
            )
            
        return response
    
    def _process_found_documents(self, related_docs, query, user_level, preferred_format):
        """
        Processa os documentos encontrados para gerar uma resposta.
        
        Args:
            related_docs: Documentos encontrados
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            
        Returns:
            Resposta formatada
        """
        # Verifica a relevância semântica dos documentos encontrados
        relevant_docs = self._filter_by_semantic_relevance(related_docs, query)
        
        if not relevant_docs:
            # Se nenhum documento for relevante o suficiente, busca mais documentos
            more_docs = self.search_service.search(query, limit=10)
            relevant_docs = self._filter_by_semantic_relevance(more_docs, query)
        
        # Seleciona trechos relevantes dos documentos
        excerpts = self._select_relevant_excerpts(
            relevant_docs, 
            query, 
            user_level, 
            preferred_format
        )
        
        # Formata a resposta
        return self._format_response(query, excerpts, user_level, preferred_format)
    
    def _search_in_all_resources(self, query):
        """
        Busca em todos os recursos disponíveis, independentemente do tipo.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Lista de documentos encontrados
        """
        all_docs = []
        
        # Tenta buscar em todos os tipos de documentos com uma consulta mais ampla
        for doc_type in ["text", "pdf", "video", "image", "json"]:
            docs = self.search_service.search_by_type(query, doc_type, limit=2)
            all_docs.extend(docs)
        
        # Se ainda não encontrou, tenta com palavras-chave extraídas da consulta
        if not all_docs:
            keywords = self._extract_topics(query)
            for keyword in keywords:
                docs = self.search_service.search(keyword, limit=2)
                all_docs.extend(docs)
                if len(all_docs) >= 3:  # Limita a 3 documentos
                    break
        
        # Remove duplicatas (baseado no ID do documento)
        unique_docs = []
        seen_ids = set()
        for doc in all_docs:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _filter_by_semantic_relevance(
        self,
        documents: List[Document],
        query: str,
        threshold: float = 0.2  # Reduzido o threshold para capturar mais documentos
    ) -> List[Document]:
        """
        Filtra documentos por relevância semântica.
        
        Args:
            documents: Lista de documentos
            query: Consulta do usuário
            threshold: Limiar de relevância (0-1)
            
        Returns:
            Lista de documentos relevantes
        """
        # Extrai palavras-chave da consulta
        keywords = set(self._extract_topics(query))
        
        # Verifica cada documento
        relevant_docs = []
        for doc in documents:
            # Conta quantas palavras-chave aparecem no conteúdo
            matches = 0
            for keyword in keywords:
                if keyword.lower() in doc.content.lower():
                    matches += 1
            
            # Calcula a relevância
            if keywords:
                relevance = matches / len(keywords)
            else:
                relevance = 0
                
            # Adiciona o documento se for relevante
            if relevance >= threshold:
                relevant_docs.append(doc)
                
        return relevant_docs
    
    def _select_relevant_excerpts(
        self, 
        documents: List[Document],
        query: str,
        user_level: str,
        preferred_format: str
    ) -> List[Tuple[Document, str]]:
        """
        Seleciona trechos relevantes dos documentos.
        
        Args:
            documents: Lista de documentos
            query: Consulta do usuário
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            
        Returns:
            Lista de tuplas (documento, trecho relevante)
        """
        if not documents:
            return []
        
        # Extrai palavras-chave da consulta
        keywords = set(self._extract_keywords(query))
        
        # Define o tamanho do trecho com base no nível do usuário
        excerpt_size = self._get_excerpt_size(user_level)
        
        # Lista para armazenar os trechos selecionados
        excerpts = []
        
        # Primeiro, prioriza documentos do formato preferido
        prioritized_docs = []
        other_docs = []
        
        for doc in documents:
            # Verifica se o arquivo existe
            source_path = self._extract_source(doc)
            if source_path and os.path.exists(source_path):
                if self._matches_preferred_format(doc, preferred_format):
                    prioritized_docs.append(doc)
                else:
                    other_docs.append(doc)
        
        # Combina as listas, com os documentos priorizados primeiro
        sorted_docs = prioritized_docs + other_docs
        
        # Limita a quantidade de documentos para não sobrecarregar
        max_docs = min(5, len(sorted_docs))
        
        # Seleciona trechos dos documentos priorizados
        for doc in sorted_docs[:max_docs]:
            # Extrai um trecho relevante do conteúdo
            excerpt = self._extract_relevant_excerpt(doc.content, keywords, excerpt_size)
            
            # Adiciona o documento e o trecho à lista
            excerpts.append((doc, excerpt))
        
        return excerpts
    
    def _format_response(
        self, 
        query: str, 
        excerpts: List[Tuple[Document, str]],
        user_level: str,
        preferred_format: str
    ) -> str:
        """
        Formata a resposta com base nos trechos selecionados.
        
        Args:
            query: Consulta do usuário
            excerpts: Lista de tuplas (documento, trecho relevante)
            user_level: Nível de conhecimento do usuário
            preferred_format: Formato preferido de conteúdo
            
        Returns:
            Resposta formatada com estrutura clara, tópicos e destaques
        """
        if not excerpts:
            return self._generate_not_found_response(query)
        
        # Extrai palavras-chave da consulta para melhorar a busca em contexto
        search_terms = self._extract_topics(query)
        
        # Melhoria: Adicionar termos relacionados para busca mais ampla
        expanded_search_terms = set(search_terms)
        for term in search_terms:
            # Adiciona variações do termo para busca mais eficiente
            expanded_search_terms.add(term.lower())
            expanded_search_terms.add(term.capitalize())
            if term.lower() in self.QUERY_EXPANSION:
                expanded_search_terms.update(self.QUERY_EXPANSION[term.lower()])
            
           
            if term.lower() in ["html", "body", "head", "footer", "header", "div"]:
                expanded_search_terms.add(f"<{term}>")
                expanded_search_terms.add(f"<{term.lower()}>")
                expanded_search_terms.add(f"tag {term}")
                expanded_search_terms.add(f"elemento {term}")
        
      
        response_parts = []
        
        # Verificar qual o tipo de documento disponível (para formatos não textuais)
        has_video = any(doc.doc_type == DocumentType.VIDEO for doc, _ in excerpts)
        has_audio = any(doc.doc_type == DocumentType.AUDIO for doc, _ in excerpts)
        has_image = any(doc.doc_type == DocumentType.IMAGE for doc, _ in excerpts)
        
       
        main_title = f"✅ **{query.capitalize()}:**"
        response_parts.append(main_title)
        
      
        combined_content = ""
        media_files = []
        
        # Reúne todo o conteúdo textual
        for _, excerpt in excerpts:
            if excerpt and len(excerpt.strip()) > 0:
                combined_content += excerpt.strip() + " "
        
        # Adiciona arquivos de mídia encontrados
        for doc, _ in excerpts:
            file_path = self._extract_source(doc)
            if file_path and os.path.exists(file_path):
                # Registra o caminho do arquivo para incluir no final
                if doc.doc_type == DocumentType.VIDEO:
                    media_files.append((file_path, "video"))
                elif doc.doc_type == DocumentType.AUDIO:
                    media_files.append((file_path, "audio"))
                elif doc.doc_type == DocumentType.IMAGE:
                    media_files.append((file_path, "image"))
        
        # Remove possíveis quebras de linha no texto para criar parágrafos melhores
        combined_content = combined_content.replace("\n", " ").strip()
        
        # Divide o conteúdo em parágrafos
        paragraphs = []
        current_len = 0
        current_para = ""
        
        for sentence in combined_content.split(". "):
            if sentence:
                if current_len > 250:  # Limita parágrafos a ~250 caracteres
                    paragraphs.append(current_para)
                    current_para = sentence + ". "
                    current_len = len(current_para)
                else:
                    current_para += sentence + ". "
                    current_len += len(sentence) + 2
        
        if current_para:
            paragraphs.append(current_para)
        
        # Adiciona os parágrafos à resposta
        for para in paragraphs:
            response_parts.append(para)
            response_parts.append("")  # Linha em branco entre parágrafos
        
        # Adiciona os arquivos de mídia no formato especial que o frontend pode detectar
        if media_files:
            if has_video:
                video_paths = [path for path, type in media_files if type == "video"]
                if video_paths:
                    response_parts.append("<!-- file_path: " + video_paths[0] + " -->")
                    response_parts.append("📺 **Assista ao vídeo sobre este tema para visualizar melhor o conteúdo.**")
                    response_parts.append("")
            
            if has_audio:
                audio_paths = [path for path, type in media_files if type == "audio"]
                if audio_paths:
                    response_parts.append("<!-- file_path: " + audio_paths[0] + " -->")
                    response_parts.append("🔊 **Ouça a explicação em áudio para entender melhor o tema.**")
                    response_parts.append("")
            
            if has_image:
                image_paths = [path for path, type in media_files if type == "image"]
                if image_paths:
                    response_parts.append("<!-- file_path: " + image_paths[0] + " -->")
                    response_parts.append("🖼️ **Veja a imagem relacionada a este tema para melhor compreensão.**")
                    response_parts.append("")
        
        # Adicionar fontes usadas (de forma mais sutil)
        response_parts.append("📚 **Fontes consultadas:**")
        
        # Adicionar fontes usadas
        unique_docs = {}
        for doc, _ in excerpts:
            if doc.id not in unique_docs:
                unique_docs[doc.id] = doc
                
        for i, doc in enumerate(unique_docs.values(), 1):
            doc_type = self._get_document_type_name(doc.doc_type)
            doc_name = self._extract_title(doc)
            response_parts.append(f"{i}. {doc_type}: {doc_name}")
        
        # Adicionar dica para o usuário aprofundar o conteúdo
        response_parts.append("\n🧐 **Posso aprofundar algum ponto específico sobre este tema?**")
        
        # Juntar todas as partes
        response = "\n".join(response_parts)
        
        return response
    
    def _perform_deep_search(self, query: str, preferred_format: str) -> str:
        """
        Realiza uma busca mais profunda nos documentos quando a busca normal não encontra resultados específicos.
        
        Args:
            query: Consulta original do usuário
            preferred_format: Formato preferido de conteúdo
            
        Returns:
            String com conteúdo adicional encontrado na busca profunda
        """
        # Extrai termos para busca profunda
        search_terms = set(self._extract_topics(query))
        
        # Adiciona variações importantes para HTML e tags
        if any(term.lower() in ["html", "body", "head", "tag", "elemento"] for term in search_terms):
            search_terms.update(["tag", "elemento", "html5", "estrutura", "documento"])
            # Para termos específicos de tags HTML
            for term in list(search_terms):
                if term.lower() in ["body", "head", "header", "footer", "section"]:
                    search_terms.add(f"<{term}>")
                    search_terms.add(f"tag {term}")
        
        # Monta uma consulta expandida para busca
        expanded_query = " OR ".join(search_terms)
        
        # Realiza a busca aprofundada no repositório
        docs = self.search_service.search(expanded_query, limit=10)
        
        # Filtra por relevância e extrai trechos importantes
        results = []
        for doc in docs:
            # Busca por menções dos termos específicos no conteúdo
            content = doc.content.lower()
            
            # Para cada termo de busca, encontra o contexto ao redor
            for term in search_terms:
                term_lower = term.lower()
                # Ignora termos muito curtos
                if len(term_lower) < 3:
                    continue
                    
                # Localiza posições do termo no conteúdo
                pos = content.find(term_lower)
                if pos >= 0:
                    # Extrai o contexto (até 200 caracteres)
                    start = max(0, pos - 100)
                    end = min(len(content), pos + 100)
                    
                    # Ajusta para não cortar palavras
                    while start > 0 and content[start] != ' ':
                        start -= 1
                    while end < len(content) and content[end] != ' ':
                        end += 1
                    
                    # Extrai o contexto e formata
                    context = content[start:end].strip()
                    # Capitaliza a primeira letra
                    if context:
                        context = context[0].upper() + context[1:]
                    
                    # Verifica se já existe um resultado similar para evitar duplicações
                    is_duplicate = False
                    for existing in results:
                        if self._calculate_similarity(context, existing["context"]) > 0.7:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        results.append({
                            "term": term,
                            "context": context,
                            "doc_type": doc.doc_type,
                            "doc_id": doc.id
                        })
        
        # Se não encontrou resultados adicionais, retorna string vazia
        if not results:
            return ""
        
        # Formata os resultados
        formatted_results = []
        for i, result in enumerate(results[:3], 1):  # Limita a 3 resultados para não sobrecarregar
            doc_type = self._get_document_type_name(result["doc_type"])
            context = result["context"]
            formatted_results.append(f"{i}. {context}\n   (Fonte: {doc_type})")
        
        return "\n".join(formatted_results)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula uma métrica simples de similaridade entre dois textos.
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Valor entre 0 e 1 representando a similaridade
        """
        # Implementação simples usando Jaccard similarity
        if not text1 or not text2:
            return 0.0
            
        # Tokeniza em palavras
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calcula a similaridade
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
    
    def _get_document_type_name(self, doc_type: DocumentType) -> str:
        """
        Retorna o nome amigável do tipo de documento.
        
        Args:
            doc_type: Tipo de documento
            
        Returns:
            Nome amigável do tipo de documento
        """
        type_names = {
            DocumentType.TEXT: "Texto",
            DocumentType.PDF: "Pdf",
            DocumentType.VIDEO: "Vídeo",
            DocumentType.IMAGE: "Imagem",
            DocumentType.JSON: "Json"
        }
        return type_names.get(doc_type, "Documento")
    
    def _extract_title(self, document: Document) -> str:
        """
        Extrai o título de um documento.
        
        Args:
            document: Documento
            
        Returns:
            Título do documento ou ID se não encontrado
        """
        # Tentar extrair do metadata
        if document.metadata:
            if "title" in document.metadata:
                return document.metadata["title"]
            elif "source" in document.metadata:
                # Extrai o nome do arquivo da fonte
                filename = os.path.basename(document.metadata["source"])
                return filename
                
        # Para documentos JSON, tenta extrair o nome ou título do conteúdo
        if document.doc_type == DocumentType.JSON:
            name_match = re.search(r'name:\s+([^,\n]+)', document.content)
            title_match = re.search(r'title:\s+([^,\n]+)', document.content)
            
            if name_match:
                return name_match.group(1).strip()
            elif title_match:
                return title_match.group(1).strip()
        
        # Usar as primeiras palavras do conteúdo como título
        words = document.content.split()
        if len(words) > 5:
            return " ".join(words[:5]) + "..."
        else:
            return document.id
    
    def _extract_preview(self, content: str, max_length: int = 100) -> str:
        """
        Extrai uma prévia do conteúdo.
        
        Args:
            content: Conteúdo do documento
            max_length: Tamanho máximo da prévia
            
        Returns:
            Prévia do conteúdo
        """
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."
    
    def _extract_source(self, document: Document) -> str:
        """
        Extrai a fonte de um documento.
        
        Args:
            document: Documento
            
        Returns:
            Fonte do documento ou vazio se não encontrada
        """
        if document.metadata and "source" in document.metadata:
            source_path = document.metadata["source"]
            
            # Verifica se o caminho existe
            if os.path.exists(source_path):
                return source_path
            
            # Se não existir, tenta encontrar um caminho correspondente na estrutura de diretórios processados
            file_name = os.path.basename(source_path)
            
            # Mapeia o tipo de documento para o diretório correspondente
            dir_mapping = {
                DocumentType.TEXT: "text",
                DocumentType.PDF: "text",  # PDFs processados são armazenados como texto
                DocumentType.VIDEO: "videos",
                DocumentType.IMAGE: "images",
                DocumentType.AUDIO: "audio",
                DocumentType.JSON: "text"  # JSONs processados são armazenados como texto
            }
            
            if document.doc_type in dir_mapping:
                subdir = dir_mapping[document.doc_type]
                corrected_path = os.path.join(str(self.resources_dir), subdir, file_name)
                
                if os.path.exists(corrected_path):
                    return corrected_path
            
            # Se ainda não encontrou, retorna o caminho do diretório processed_data
            return str(self.resources_dir)
            
        return ""
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extrai palavras-chave de uma consulta.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Lista de palavras-chave
        """
        # Remover pontuação e dividir em palavras
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Remover stop words simples em português
        stop_words = {
            "a", "o", "e", "de", "da", "do", "em", "um", "uma", "que", "é",
            "para", "com", "por", "como", "mas", "se", "no", "na", "os", "as",
            "me", "explique", "sobre", "quais", "são", "como", "funciona",
            "quem", "onde", "quando", "tem", "ter", "há", "esse", "essa",
            "isto", "isso", "aquilo", "este", "esta", "meu", "minha", "seu", "sua"
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def _matches_preferred_format(self, document: Document, preferred_format: str) -> bool:
        """
        Verifica se o documento corresponde ao formato preferido.
        
        Args:
            document: Documento
            preferred_format: Formato preferido
            
        Returns:
            True se corresponder, False caso contrário
        """
        # Mapeamento de formatos para tipos de documento
        format_mapping = {
            "texto": [DocumentType.TEXT, DocumentType.PDF, DocumentType.JSON],
            "vídeo": [DocumentType.VIDEO],
            "video": [DocumentType.VIDEO],
            "imagem": [DocumentType.IMAGE],
            "image": [DocumentType.IMAGE],
            "áudio": [DocumentType.AUDIO],
            "audio": [DocumentType.AUDIO]
        }
        
        # Normaliza o formato preferido
        preferred_format_lower = preferred_format.lower()
        
        # Verifica se o formato está no mapeamento
        if preferred_format_lower in format_mapping:
            return document.doc_type in format_mapping[preferred_format_lower]
        
        # Se o formato não for reconhecido, assume texto como padrão
        return document.doc_type in [DocumentType.TEXT, DocumentType.PDF, DocumentType.JSON]
    
    def _get_excerpt_size(self, user_level: str) -> int:
        """
        Define o tamanho do trecho com base no nível do usuário.
        
        Args:
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Tamanho do trecho em caracteres
        """
        if user_level == "iniciante":
            return 200  # Trechos curtos para iniciantes
        elif user_level == "intermediário":
            return 400  # Trechos médios para nível intermediário
        else:  # avançado
            return 800  # Trechos maiores para usuários avançados
    
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
            return content[:max_length]
        
        # Calcula a relevância de cada parágrafo
        paragraph_scores = []
        for p in paragraphs:
            score = 0
            for keyword in keywords:
                if keyword.lower() in p.lower():
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
                    return paragraph_scores[0][0][:max_length]
                break
                
            selected_paragraphs.append(p)
            current_length += len(p) + 2  # +2 para "\n\n"
            
        # Junta os parágrafos selecionados
        return "\n\n".join(selected_paragraphs)
    
    def analyze_user_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Analisa o histórico de interações do usuário para identificar padrões de aprendizagem.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com análise de padrões e recomendações
        """
        user_progress = self.user_progress_repository.get_by_id(user_id)
        if not user_progress or not user_progress.interactions:
            return {"status": "insufficient_data"}
        
        # Análise de interações recentes (últimas 10)
        recent_interactions = user_progress.get_recent_interactions(10)
        
        # Extrai tópicos das consultas recentes
        topics_frequency = {}
        for interaction in recent_interactions:
            topics = self._extract_topics(interaction.query)
            for topic in topics:
                topics_frequency[topic] = topics_frequency.get(topic, 0) + 1
        
        # Identifica tópicos mais frequentes
        frequent_topics = sorted(
            topics_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        # Analisa dificuldades com base no feedback
        difficulty_topics = []
        for interaction in recent_interactions:
            if interaction.feedback and "negativ" in interaction.feedback.lower():
                topics = self._extract_topics(interaction.query)
                difficulty_topics.extend(topics)
        
        # Identifica o formato preferido com base nas interações
        preferred_format = self._infer_learning_style(recent_interactions)
        
        return {
            "status": "success",
            "frequent_topics": [topic for topic, _ in frequent_topics],
            "difficulty_topics": list(set(difficulty_topics)),
            "learning_style": preferred_format or user_progress.profile.preferred_format,
            "recommendations": self._generate_learning_recommendations(
                frequent_topics, 
                difficulty_topics, 
                user_progress.profile.level
            )
        }
    
    def _infer_learning_style(self, interactions: List[UserInteraction]) -> Optional[str]:
        """
        Infere o estilo de aprendizagem com base nas interações.
        
        Args:
            interactions: Lista de interações do usuário
            
        Returns:
            Estilo de aprendizagem inferido ou None
        """
        # Implementação simples: analisa preferência por tipo de conteúdo
        content_preference = {"texto": 0, "vídeo": 0, "imagem": 0}
        
        for interaction in interactions:
            # Analisa a consulta por menções a formatos
            query = interaction.query.lower()
            if "vídeo" in query or "video" in query or "assistir" in query or "ver" in query:
                content_preference["vídeo"] += 1
            elif "imagem" in query or "figura" in query or "visual" in query or "diagrama" in query:
                content_preference["imagem"] += 1
            else:
                content_preference["texto"] += 1
        
        # Determina se há uma preferência clara
        # (pelo menos 50% mais que a média dos outros)
        max_preference = max(content_preference.items(), key=lambda x: x[1])
        values = list(content_preference.values())
        avg_others = (sum(values) - max_preference[1]) / (len(values) - 1) if len(values) > 1 else 0
        
        if max_preference[1] > 0 and max_preference[1] >= avg_others * 1.5:
            return max_preference[0]
        
        return None
    
    def _generate_learning_recommendations(
        self,
        frequent_topics: List[Tuple[str, int]],
        difficulty_topics: List[str],
        user_level: str
    ) -> List[Dict[str, Any]]:
        """
        Gera recomendações de aprendizado com base nos padrões detectados.
        
        Args:
            frequent_topics: Lista de tópicos frequentes com contagem
            difficulty_topics: Lista de tópicos com dificuldades
            user_level: Nível de conhecimento do usuário
            
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        # Adiciona recomendações para tópicos com dificuldade
        if difficulty_topics:
            # Reduz o nível para tópicos difíceis
            effective_level = "iniciante" if user_level != "iniciante" else "iniciante"
            
            # Busca conteúdos mais simples para os tópicos difíceis
            for topic in difficulty_topics[:2]:  # Limita a 2 tópicos difíceis
                query = f"entender {topic} explicação simples"
                topic_suggestions = self.suggest_related_content(
                    query=query,
                    user_level=effective_level,
                    limit=1
                )
                
                if topic_suggestions:
                    for suggestion in topic_suggestions:
                        suggestion["reason"] = f"Para ajudar com dificuldades sobre {topic}"
                        recommendations.append(suggestion)
        
        # Adiciona recomendações para aprofundar nos tópicos frequentes
        if frequent_topics:
            # Aumenta o nível para tópicos frequentes (se não for avançado)
            effective_level = "avançado" if user_level != "avançado" else "avançado"
            
            # Busca conteúdos mais avançados para os tópicos frequentes
            for topic, _ in frequent_topics[:2]:  # Limita a 2 tópicos frequentes
                query = f"{topic} avançado conceitos aprofundados"
                topic_suggestions = self.suggest_related_content(
                    query=query,
                    user_level=effective_level,
                    limit=1
                )
                
                if topic_suggestions:
                    for suggestion in topic_suggestions:
                        suggestion["reason"] = f"Para aprofundar seus conhecimentos em {topic}"
                        recommendations.append(suggestion)
        
        # Adiciona recomendação para tópicos relacionados
        if frequent_topics:
            # Extrai palavras-chave dos tópicos frequentes
            topic_words = [topic for topic, _ in frequent_topics]
            related_query = " ".join([t for t in topic_words if t])
            
            if related_query:
                # Busca tópicos relacionados
                related_suggestions = self.suggest_related_content(
                    query=f"{related_query} tópicos relacionados",
                    user_level=user_level,
                    limit=2
                )
                
                if related_suggestions:
                    for suggestion in related_suggestions:
                        suggestion["reason"] = "Conteúdo relacionado aos seus interesses"
                        recommendations.append(suggestion)
        
        return recommendations[:5]  # Limita a 5 recomendações no total
    
    def suggest_proactive_content(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Sugere conteúdos proativamente com base no histórico do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de conteúdos sugeridos
        """
        # Analisa padrões de aprendizagem
        patterns = self.analyze_user_learning_patterns(user_id)
        
        if patterns["status"] == "insufficient_data":
            # Se não há dados suficientes, retorna recomendações genéricas
            return self.suggest_related_content("aprendizagem adaptativa", limit=3)
        
        # Se já temos recomendações baseadas em padrões, usa-as
        if "recommendations" in patterns and patterns["recommendations"]:
            return patterns["recommendations"]
        
        # Caso contrário, combina tópicos frequentes e tópicos com dificuldade para gerar sugestões
        all_topics = patterns.get("frequent_topics", []) + patterns.get("difficulty_topics", [])
        
        # Remove duplicatas mantendo a ordem
        unique_topics = []
        for topic in all_topics:
            if topic not in unique_topics:
                unique_topics.append(topic)
        
        # Limita a 3 tópicos para busca
        search_topics = unique_topics[:3]
        
        # Se não houver tópicos suficientes, usa um termo genérico
        if not search_topics:
            search_topics = ["aprendizagem", "educação", "tecnologia"]
        
        # Prepara a consulta combinada
        combined_query = " ".join(search_topics)
        
        # Busca conteúdos relacionados aos tópicos
        results = self.suggest_related_content(
            combined_query, 
            user_level=patterns.get("learning_style", "intermediário"),
            limit=5
        )
        
        # Adiciona a razão da recomendação
        for item in results:
            item["reason"] = "Baseado em seus interesses recentes"
            
        return results
    
    def _expand_query(self, query: str) -> str:
        """
        Expande a consulta com termos relacionados.
        
        Args:
            query: Consulta original
            
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
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extrai tópicos relevantes de um texto.
        
        Args:
            text: Texto para extração de tópicos
            
        Returns:
            Lista de tópicos extraídos
        """
        # Tokeniza o texto
        words = re.findall(r'\b\w+\b', text.lower())
        
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
        
        # Remove duplicatas mantendo a ordem
        unique_topics = []
        for topic in topics:
            if topic not in unique_topics:
                unique_topics.append(topic)
                
        return unique_topics
    
    def _suggest_related_topics(self, query: str) -> List[str]:
        """
        Sugere tópicos relacionados à consulta.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Lista de tópicos relacionados
        """
        # Mapeamento de tópicos para sugestões relacionadas
        related_topics_map = {
            "html": ["Estrutura básica HTML5", "Tags semânticas", "Formulários HTML5", "Links e âncoras", "Tabelas HTML"],
            "css": ["Seletores CSS", "Box model", "Flexbox", "Grid layout", "Responsividade"],
            "javascript": ["Variáveis e tipos", "Funções", "DOM", "Eventos", "Promises"],
            "web": ["HTML5", "CSS3", "JavaScript", "Responsividade", "Acessibilidade"],
            "página": ["Estrutura HTML", "Cabeçalho e rodapé", "Navegação", "Conteúdo principal", "Seções"],
            "estrutura": ["DOCTYPE", "HTML", "Head", "Body", "Elementos semânticos"],
            "tabela": ["Table", "TR", "TD", "TH", "Caption"],
            "lista": ["UL", "OL", "LI", "DL", "Listas aninhadas"],
            "formulário": ["Form", "Input", "Select", "Textarea", "Button"],
            "texto": ["Headings", "Parágrafos", "Formatação", "Citações", "Código"]
        }
        
        # Extrai tópicos da consulta
        topics = self._extract_topics(query)
        
        # Coleta sugestões para os tópicos identificados
        suggestions = []
        for topic in topics:
            for key, values in related_topics_map.items():
                if topic in key or key in topic:
                    suggestions.extend(values)
                    break
        
        # Se não encontrou sugestões específicas, usa sugestões gerais de HTML
        if not suggestions:
            suggestions = [
                "Estrutura básica HTML5",
                "Tags semânticas HTML5",
                "Formatação de texto em HTML",
                "Listas e tabelas em HTML",
                "Formulários HTML5"
            ]
        
        # Remove duplicatas mantendo a ordem
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
                
        return unique_suggestions[:5]  # Retorna até 5 sugestões
    
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
        related_docs = self.search_service.search(expanded_query, limit=limit+2)  # Busca alguns a mais para ter variedade
        
        # Se não encontrar com a consulta expandida, tenta com a consulta original
        if not related_docs:
            related_docs = self.search_service.search(query, limit=limit+2)
        
        # Se ainda não encontrou, tenta com tópicos relacionados
        if not related_docs:
            topics = self._suggest_related_topics(query)
            for topic in topics:
                docs = self.search_service.search(topic, limit=2)
                related_docs.extend(docs)
                if len(related_docs) >= limit+2:
                    break
        
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
            
            # Obtém o caminho correto do arquivo
            source_path = self._extract_source(doc)
            
            # Verifica se o arquivo existe (não usa arquivos de amostra)
            if source_path and os.path.exists(source_path):
                # Cria o item de conteúdo relacionado
                content_item = {
                    "id": doc.id,
                    "title": title,
                    "type": doc.doc_type.value,
                    "preview": self._extract_preview(doc.content),
                    "source": source_path
                }
                
                related_content.append(content_item)
                
                # Limita ao número solicitado
                if len(related_content) >= limit:
                    break
                    
        return related_content
    
    def _generate_not_found_response(self, query: str) -> str:
        """
        Gera uma resposta quando não são encontrados documentos relevantes.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Resposta formatada
        """
        return (
            f"Não sei responder exatamente sua pergunta, mas aqui está uma provável resposta com base nos recursos disponíveis:\n\n"
            f"Infelizmente, não encontrei informações específicas sobre este tópico nos recursos disponíveis. Tente outra pergunta."
        )
    
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
            
        return self.user_progress_repository.update_interaction(
            user_id=user_id,
            query=query,
            response=response,
            feedback=feedback
        ) 