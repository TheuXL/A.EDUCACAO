#!/usr/bin/env python3
"""
Console para testar o sistema de resposta adaptativa.
Execute este script diretamente para interagir com o sistema.
"""
import os
import sys
import time
from pathlib import Path

# Configuração do path para importar corretamente os módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

import chromadb
from app.application.services.indexer_service import IndexerService
from app.application.services.prompt_service import PromptServiceImpl
from app.domain.usecases.generate_adaptive_response_usecase import GenerateAdaptiveResponseUseCase
from app.infrastructure.repositories.json_user_progress_repository import JsonUserProgressRepository
from app.domain.entities.user_session import UserSession

# Cores ANSI para formatação do terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}{text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}{text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}{text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}{text}{Colors.ENDC}")

def show_progress(duration=2):
    """Mostra um indicador de progresso"""
    progress_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = time.time()
    i = 0
    
    while time.time() - start_time < duration:
        sys.stdout.write(f"\r{Colors.BLUE}Gerando resposta adaptativa... {progress_chars[i % len(progress_chars)]}{Colors.ENDC}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def suppress_output(func):
    """Decorador para suprimir saídas de debug"""
    def wrapper(*args, **kwargs):
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            result = func(*args, **kwargs)
        finally:
            sys.stdout.close()
            sys.stdout = original_stdout
        return result
    return wrapper

class AdaptiveResponseConsole:
    """
    Console interativo para o sistema de resposta adaptativa.
    Permite ao usuário interagir com o sistema, fazer consultas e receber respostas personalizadas.
    """
    
    def __init__(self):
        """Inicializa o console interativo"""
        # Inicializa a sessão do usuário
        self.session = UserSession()
        
        # Níveis de usuário disponíveis
        self.user_levels = ["iniciante", "intermediário", "avançado"]
        
        # Formatos preferidos disponíveis
        self.preferred_formats = ["texto", "vídeo", "imagem"]
        
        # Configuração do ChromaDB
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.chroma_dir = os.path.join(self.base_dir, "database", "chromadb")
        
        # Inicialização dos serviços
        self._init_services()
        
    def _init_services(self):
        """Inicializa os serviços necessários para o funcionamento do console"""
        # Verifica se o diretório ChromaDB existe
        if not os.path.exists(self.chroma_dir):
            print_error(f"Erro: Diretório ChromaDB não encontrado: {self.chroma_dir}")
            print_warning("Execute primeiro o script de indexação (index_resources.py).")
            sys.exit(1)
            
        # Cliente ChromaDB
        @suppress_output
        def init_chroma():
            return chromadb.PersistentClient(path=self.chroma_dir)
        
        self.chroma_client = init_chroma()
        
        # Serviço de indexação
        @suppress_output
        def init_indexer():
            return IndexerService(
                chroma_client=self.chroma_client,
                collection_name="a_educacao"
            )
        
        self.indexer_service = init_indexer()
        
        # Repositório de progresso do usuário
        self.user_progress_repository = JsonUserProgressRepository()
        
        # Serviço de prompt
        self.prompt_service = PromptServiceImpl(
            search_service=self.indexer_service.search_service,
            user_progress_repository=self.user_progress_repository
        )
        
        # Caso de uso para geração de respostas adaptativas
        self.adaptive_response_usecase = GenerateAdaptiveResponseUseCase(
            prompt_service=self.prompt_service
        )
    
    def process_query(self, query):
        """
        Processa uma consulta do usuário e gera uma resposta adaptativa.
        
        Args:
            query: A pergunta do usuário
        """
        # Atualiza o contexto da sessão
        self.session.add_to_context(query)
        
        print("\n" + "="*80)
        print_header(f"CONSULTA: '{query}'")
        print_info(f"NÍVEL DO USUÁRIO: {self.session.user_level}")
        print_info(f"FORMATO PREFERIDO: {self.session.preferred_format}")
        print("="*80 + "\n")
        
        try:
            # Gera a resposta
            print_info("🔍 Gerando resposta adaptativa...")
            show_progress()
            
            @suppress_output
            def generate_response():
                return self.adaptive_response_usecase.generate_response(
                    query=query,
                    user_level=self.session.user_level,
                    preferred_format=self.session.preferred_format,
                    user_id=self.session.user_id
                )
            
            response = generate_response()
            
            # Armazena a resposta na sessão
            self.session.store_response(response)
            
            # Exibe a resposta
            print(response)
            
            # Oferece opções para o usuário
            self.get_user_feedback()
                
        except Exception as e:
            print_error(f"Erro ao gerar resposta: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_user_feedback(self):
        """Obtém feedback do usuário sobre a resposta"""
        print_header("\nO que você gostaria de fazer agora?")
        print(f"1. {Colors.GREEN}Esta resposta foi útil{Colors.ENDC}")
        print(f"2. {Colors.RED}Esta resposta não foi útil{Colors.ENDC}")
        print(f"3. {Colors.BLUE}Aprofundar esta explicação{Colors.ENDC}")
        print(f"4. {Colors.BLUE}Trazer mais conteúdos relacionados{Colors.ENDC}")
        print(f"5. {Colors.YELLOW}Continuar{Colors.ENDC}")
        
        choice = input(f"\n{Colors.GREEN}Escolha uma opção (1-5):{Colors.ENDC} ")
        
        # Processar a escolha do usuário
        if choice == "1":
            # Feedback positivo
            print_success("Obrigado pelo feedback positivo!")
            self.prompt_service.store_user_interaction(
                user_id=self.session.user_id,
                query=self.session.last_query,
                response=self.session.last_response,
                feedback="positivo"
            )
        elif choice == "2":
            # Feedback negativo
            print_warning("Lamentamos que a resposta não tenha sido útil.")
            self.prompt_service.store_user_interaction(
                user_id=self.session.user_id,
                query=self.session.last_query,
                response=self.session.last_response,
                feedback="negativo"
            )
            
            # Pedir sugestão de melhoria
            suggestion = input(f"\n{Colors.YELLOW}Como poderíamos melhorar esta resposta?{Colors.ENDC} ")
            if suggestion.strip():
                # Validar que a sugestão tem conteúdo significativo
                if len(suggestion) > 10:
                    print_success("Obrigado pela sugestão detalhada! Vamos trabalhar para melhorar.")
                    # Aqui poderia salvar a sugestão em um log específico
                else:
                    print_success("Obrigado pelo feedback! Tente ser mais específico para nos ajudar a melhorar.")
        elif choice == "3":
            # Aprofundar a explicação
            print_info("Aprofundando a explicação...")
            new_query = f"Explique com mais detalhes: {self.session.last_query}"
            self.process_query(new_query)
        elif choice == "4":
            # Trazer mais conteúdos relacionados
            print_info("Buscando mais conteúdos relacionados...")
            new_query = f"Conteúdos relacionados a: {self.session.last_query}"
            self.process_query(new_query)
        elif choice == "5":
            # Continuar
            print_info("Continuando...")
        else:
            print_warning("Opção inválida. Continuando...")
    
    def update_user_preferences(self):
        """Permite ao usuário atualizar suas preferências"""
        print_header("\nALTERAÇÃO DE PREFERÊNCIAS")
        print_info("\nNíveis de usuário disponíveis:")
        
        for i, level in enumerate(self.user_levels, 1):
            print(f"  {Colors.BLUE}{i}.{Colors.ENDC} {level}")
            
        try:
            level_idx = int(input(f"\n{Colors.GREEN}Escolha um nível (1-3) [{self.session.user_level}]:{Colors.ENDC} ")) - 1
            if level_idx >= 0 and level_idx < len(self.user_levels):
                self.session.update_preferences(level=self.user_levels[level_idx])
                print_success(f"Nível atualizado para: {self.session.user_level}")
        except ValueError:
            print_info(f"Mantendo o nível atual: {self.session.user_level}")
            
        print_info("\nFormatos preferidos disponíveis:")
        for i, format_name in enumerate(self.preferred_formats, 1):
            print(f"  {Colors.BLUE}{i}.{Colors.ENDC} {format_name}")
            
        try:
            format_idx = int(input(f"\n{Colors.GREEN}Escolha um formato (1-3) [{self.session.preferred_format}]:{Colors.ENDC} ")) - 1
            if format_idx >= 0 and format_idx < len(self.preferred_formats):
                self.session.update_preferences(format=self.preferred_formats[format_idx])
                print_success(f"Formato preferido atualizado para: {self.session.preferred_format}")
        except ValueError:
            print_info(f"Mantendo o formato atual: {self.session.preferred_format}")
    
    def run(self):
        """Inicia o console interativo"""
        print_header("SISTEMA DE APRENDIZAGEM ADAPTATIVA +A EDUCAÇÃO")
        print_info("Este sistema oferece respostas personalizadas com base no seu nível e preferências.")
        
        # Menu para o usuário
        while True:
            print_header("\nMENU PRINCIPAL")
            print(f"1. {Colors.BLUE}Fazer uma consulta{Colors.ENDC}")
            print(f"2. {Colors.BLUE}Alterar minhas preferências{Colors.ENDC}")
            print(f"3. {Colors.YELLOW}Sair{Colors.ENDC}")
            
            choice = input(f"\n{Colors.GREEN}Escolha uma opção (1-3):{Colors.ENDC} ")
            
            if choice == "1":
                query = input(f"\n{Colors.GREEN}Digite sua consulta:{Colors.ENDC} ")
                if not query.strip():
                    print_error("A consulta não pode estar vazia.")
                    continue
                
                # Executa a consulta
                self.process_query(query)
                    
            elif choice == "2":
                self.update_user_preferences()
                    
            elif choice == "3":
                print_success("Saindo... Obrigado por usar o Sistema de Aprendizagem Adaptativa!")
                break
                
            else:
                print_error("Opção inválida.")
                continue

def main():
    """Função principal"""
    console = AdaptiveResponseConsole()
    console.run()

if __name__ == "__main__":
    main() 