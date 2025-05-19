import os
from app.api import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Use este arquivo para iniciar diretamente com o Uvicorn através da linha de comando:
    # uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    
    # Ou importe a variável 'app' em outros módulos
    print(f"A aplicação FastAPI está pronta para ser servida em http://{host}:{port}")
    print("Use 'uvicorn app.main:app --reload' para iniciar o servidor.") 