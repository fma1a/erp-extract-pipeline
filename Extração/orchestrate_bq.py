"""
ORCHESTRATE_BQ
--------------
Encadeia a extracao e a carga no BigQuery: so roda o load_bq.py se o
extract.py terminar sem erro. Mesmo padrao do orchestrate.py (Snowflake),
so trocando o destino da carga.
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
    print(f"[OK] {script_name} concluido.")


if __name__ == "__main__":
    run_step("extract.py")
    run_step("load_bq.py")
    print(f"\n=== [{datetime.now()}] Pipeline BigQuery (extracao+carga) concluido com sucesso ===")