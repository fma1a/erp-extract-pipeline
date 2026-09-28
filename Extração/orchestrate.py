"""
ORCHESTRATE
-----------
Encadeia a extração e a carga: só roda o load.py se o extract.py
terminar sem erro. Pensado pra ser chamado pelo Agendador de Tarefas
do Windows, sem precisar de ninguém clicando em nada.
"""

import subprocess
import sys
from datetime import datetime

def run_step(script_name: str):
    print(f"\n=== [{datetime.now()}] Rodando {script_name} ===")
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        print(f"[ERRO] {script_name} falhou (exit code {result.returncode}). Abortando pipeline.")
        sys.exit(1)
    print(f"[OK] {script_name} concluído.")

if __name__ == "__main__":
    run_step("extract.py")
    run_step("load.py")
    print(f"\n=== [{datetime.now()}] Pipeline de extração+carga concluído com sucesso ===")