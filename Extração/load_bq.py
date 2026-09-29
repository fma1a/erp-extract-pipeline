"""
LOAD_BQ
-------
Le os CSVs gerados pelo extract.py (data/raw/) e carrega cada um
como uma tabela no dataset "bronze" do BigQuery, substituindo o
conteudo anterior a cada execucao (write_disposition = WRITE_TRUNCATE).

Autenticacao: usa Application Default Credentials (ADC).
- Localmente: gcloud auth application-default login
- No GitHub Actions: Workload Identity Federation (sem chave nenhuma)
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "pipeline-simulation")
DATASET = os.environ.get("GCP_BRONZE_DATASET", "bronze")
DATA_DIR = Path(__file__).parent / "data" / "raw"

TABLES = ["customers", "products", "orders", "order_items"]


def load_table(client: bigquery.Client, table_name: str):
    csv_path = DATA_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        print(f"[AVISO] Arquivo nao encontrado, pulando: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )

    print(f"Carregando {len(df)} linhas em {table_id}...")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # espera terminar
    print(f"[OK] {table_id} atualizado ({len(df)} linhas).")


def main():
    client = bigquery.Client(project=PROJECT_ID)
    for table in TABLES:
        load_table(client, table)
    print("\nCarga no BigQuery concluida.")


if __name__ == "__main__":
    main()