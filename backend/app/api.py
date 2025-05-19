import os
import uvicorn
import logging
from dotenv import load_dotenv
from pathlib import Path
import sys

# Adicionar o diretório raiz ao path do Python para permitir importações absolutas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.controllers.api_controller import ApiController


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api_server.log")
    ]
)

logger = logging.getLogger("api_server")

# Carrega variáveis de ambiente
load_dotenv()

# Cria e configura a aplicação FastAPI
logger.info("Inicializando A.Educação API com FastAPI...")
api_controller = ApiController()
app = api_controller.get_app()

# Inicia o servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Iniciando servidor Uvicorn na porta {port}...")
    
    uvicorn.run(
        "app.api:app",
        host=host,
        port=port,
        reload=True
    ) 