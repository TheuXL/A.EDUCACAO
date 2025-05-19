from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import subprocess
import json
import os
import sys
import tempfile
from pathlib import Path

router = APIRouter()

class PerformanceTestRequest(BaseModel):
    test_dir: str = "/tmp/aeducacao_test"
    api_url: str = None
    test_type: str = "all"  # 'all', 'batch', 'realtime', 'api'

@router.post("/admin/performance-test")
async def run_performance_test(request: PerformanceTestRequest):
    """Executa testes de performance do sistema"""
    
    if not os.path.exists(request.test_dir):
        try:
            os.makedirs(request.test_dir, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao criar diretório de teste: {str(e)}")
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              "tests", "performance", "stress_test.py")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script de teste não encontrado: {script_path}")
    
    cmd = [sys.executable, script_path, "--test-dir", request.test_dir]
    
    if request.api_url:
        cmd.extend(["--api-url", request.api_url])
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        results_file = tmp.name
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = process.communicate(timeout=300)  # 5 minutos de timeout
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=500, 
                detail=f"Erro ao executar teste de performance: {stderr.decode('utf-8')}"
            )
        
        results_dir = os.path.join(os.path.dirname(script_path), "results")
        report_path = os.path.join(results_dir, "performance_report.json")
        
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                results = json.load(f)
                return results
        else:
            raise HTTPException(
                status_code=500,
                detail="Arquivo de resultados não encontrado após execução do teste"
            )
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Timeout ao executar teste de performance")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar teste: {str(e)}")
    finally:
        if os.path.exists(results_file):
            os.unlink(results_file) 