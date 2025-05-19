#!/usr/bin/env python3
"""
Script para executar o console do sistema de resposta adaptativa.
Este script facilita a execução do console a partir da raiz do projeto.
"""
import os
import sys

# Adiciona o diretório atual ao sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa e executa o console de resposta adaptativa
from app.console_adaptive_response import main

if __name__ == "__main__":
    main() 