"""
LOAD
----
Carrega os CSVs de data/raw/ para as tabelas RAW no Snowflake.

Rodar (com o venv ativo):
    python load.py
"""

import os
import sys

import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

load_dotenv(os.path.join(BASE_DIR, ".env"))

REQUIRED_ENV_VARS = [
    "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA",
]

# tabela (no Snowflake) -> arquivo CSV correspondente, com colunas de data
TABLE_MAP = {
    "CUSTOMERS": ("customers.csv", ["created_at", "updated_at"]),
    "PRODUCTS": ("products.csv", []),
    "ORDERS": ("orders.csv", ["order_ts", "updated_at"]),
    "ORDER_ITEMS": ("order_items.csv", ["updated_at"]),
}


def check_env():
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        print("Faltam variáveis no .env:")
        for v in missing:
            print(f"  - {v}")
        sys.exit(1)


def get_connection():
    import snowflake.connector

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def load_table(conn, table_name: str, csv_file: str, date_cols: list):
    from snowflake.connector.pandas_tools import write_pandas

    path = os.path.join(RAW_DIR, csv_file)
    df = pd.read_csv(path)
    df.columns = [c.upper() for c in df.columns]  # Snowflake usa MAIÚSCULAS por padrão

    success, n_chunks, n_rows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name=table_name,
        auto_create_table=False,  # a tabela já existe (criamos no SQL da Etapa 2)
        overwrite=True,           # cada rodada substitui o conteúdo anterior
    )
    print(f"{table_name:<15} success={success}  rows={n_rows}")


def main():
    check_env()
    print(f"Conectando em {os.getenv('SNOWFLAKE_ACCOUNT')}...")
    conn = get_connection()

    try:
        for table_name, (csv_file, date_cols) in TABLE_MAP.items():
            load_table(conn, table_name, csv_file, date_cols)
    finally:
        conn.close()

    print("\nCarga concluída.")


if __name__ == "__main__":
    main()