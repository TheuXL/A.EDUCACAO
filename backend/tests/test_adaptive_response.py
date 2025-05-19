#!/usr/bin/env python3
import os
import sys
import uuid
import time
import chromadb
from pathlib import Path

# Adiciona o diretório pai ao path para permitir imports relativos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def test_response(query, session):
    """
    Testa a geração de resposta adaptativa para uma consulta específica.
    
    Args:
        query: A pergunta do usuário
        session: Objeto de sessão do usuário
    """
    # Atualiza o contexto da sessão
    session.add_to_context(query)
    
    print("\n" + "="*80)
    print_header(f"CONSULTA: '{query}'")
    print_info(f"NÍVEL DO USUÁRIO: {session.user_level}")
    print_info(f"FORMATO PREFERIDO: {session.preferred_format}")
    print("="*80 + "\n")
    
    # Configuração dos caminhos
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    chroma_dir = os.path.join(base_dir, "database", "chromadb")
    
    # Verifica se o diretório ChromaDB existe
    if not os.path.exists(chroma_dir):
        print_error(f"Erro: Diretório ChromaDB não encontrado: {chroma_dir}")
        print_warning("Execute primeiro o script de indexação.")
        sys.exit(1)
        
    # Inicializa os componentes necessários
    try:
        # Cliente ChromaDB
        @suppress_output
        def init_chroma():
            return chromadb.PersistentClient(path=chroma_dir)
        
        chroma_client = init_chroma()
        
        # Serviço de indexação
        @suppress_output
        def init_indexer():
            return IndexerService(
                chroma_client=chroma_client,
                collection_name="a_educacao"
            )
        
        indexer_service = init_indexer()
        
        # Repositório de progresso do usuário
        user_progress_repository = JsonUserProgressRepository()
        
        # Serviço de prompt
        prompt_service = PromptServiceImpl(
            search_service=indexer_service.search_service,
            user_progress_repository=user_progress_repository
        )
        
        # Caso de uso para geração de respostas adaptativas
        adaptive_response_usecase = GenerateAdaptiveResponseUseCase(
            prompt_service=prompt_service
        )
        
        # Gera a resposta
        print_info("🔍 Gerando resposta adaptativa...")
        show_progress()
        
        @suppress_output
        def generate_response():
            return adaptive_response_usecase.generate_response(
                query=query,
                user_level=session.user_level,
                preferred_format=session.preferred_format,
                user_id=session.user_id
            )
        
        response = generate_response()
        
        # Armazena a resposta na sessão
        session.store_response(response)
        
        # Exibe a resposta
        print(response)
        
        # Oferece opções para o usuário
        get_user_feedback(session, prompt_service)
            
    except Exception as e:
        print_error(f"Erro ao gerar resposta: {str(e)}")
        import traceback
        traceback.print_exc()

def get_user_feedback(session, prompt_service):
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
        prompt_service.store_user_interaction(
            user_id=session.user_id,
            query=session.last_query,
            response=session.last_response,
            feedback="positivo"
        )
    elif choice == "2":
        # Feedback negativo
        print_warning("Lamentamos que a resposta não tenha sido útil.")
        prompt_service.store_user_interaction(
            user_id=session.user_id,
            query=session.last_query,
            response=session.last_response,
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
        new_query = f"Explique com mais detalhes: {session.last_query}"
        test_response(new_query, session)
    elif choice == "4":
        # Trazer mais conteúdos relacionados
        print_info("Buscando mais conteúdos relacionados...")
        new_query = f"Conteúdos relacionados a: {session.last_query}"
        test_response(new_query, session)
    elif choice == "5":
        # Continuar
        print_info("Continuando...")
    else:
        print_warning("Opção inválida. Continuando...")

def main():
    """
    Função principal que executa os testes de resposta adaptativa.
    """
    # Níveis de usuário disponíveis
    user_levels = ["iniciante", "intermediário", "avançado"]
    
    # Formatos preferidos disponíveis
    preferred_formats = ["texto", "vídeo", "imagem"]
    
    # Inicializa a sessão do usuário
    session = UserSession()
    
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
            test_response(query, session)
                
        elif choice == "2":
            # Altera as preferências do usuário
            print_header("\nALTERAÇÃO DE PREFERÊNCIAS")
            print_info("\nNíveis de usuário disponíveis:")
            for i, level in enumerate(user_levels, 1):
                print(f"  {Colors.BLUE}{i}.{Colors.ENDC} {level}")
                
            try:
                level_idx = int(input(f"\n{Colors.GREEN}Escolha um nível (1-3) [{session.user_level}]:{Colors.ENDC} ")) - 1
                if level_idx >= 0 and level_idx < len(user_levels):
                    session.update_preferences(level=user_levels[level_idx])
                    print_success(f"Nível atualizado para: {session.user_level}")
            except ValueError:
                print_info(f"Mantendo o nível atual: {session.user_level}")
                
            print_info("\nFormatos preferidos disponíveis:")
            for i, format_name in enumerate(preferred_formats, 1):
                print(f"  {Colors.BLUE}{i}.{Colors.ENDC} {format_name}")
                
            try:
                format_idx = int(input(f"\n{Colors.GREEN}Escolha um formato (1-3) [{session.preferred_format}]:{Colors.ENDC} ")) - 1
                if format_idx >= 0 and format_idx < len(preferred_formats):
                    session.update_preferences(format=preferred_formats[format_idx])
                    print_success(f"Formato preferido atualizado para: {session.preferred_format}")
            except ValueError:
                print_info(f"Mantendo o formato atual: {session.preferred_format}")
                
        elif choice == "3":
            print_success("Saindo... Obrigado por usar o Sistema de Aprendizagem Adaptativa!")
            break
            
        else:
            print_error("Opção inválida.")
            continue

if __name__ == "__main__":
    main() 