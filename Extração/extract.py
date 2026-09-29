"""
EXTRACT
-------
Extrai os dados do ERP (fake, nesse treino) via API: autentica, pagina
por todos os endpoints, trata token vencido e falha intermitente, e
salva o resultado cru em CSV -- sem transformar nada ainda.

Rodar (com o venv ativo e a API fake rodando em outra janela):
    python extract.py
"""

import os
import time

import pandas as pd
import requests

from dotenv import load_dotenv
load_dotenv()
# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("ERP_BASE_URL", "http://localhost:8000")
CLIENT_ID = "erp_demo_client"
CLIENT_SECRET = "erp_demo_secret_2026"

PAGE_SIZE = 100          # quantos registros pedir por página
MAX_RETRIES = 3          # tentativas antes de desistir de uma chamada
RETRY_BACKOFF_SECONDS = 2  # espera entre tentativas

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
_auth_state = {"token": None, "expires_at": 0}


def _request_new_token():
    """Troca client_id/client_secret por um access_token novo."""
    response = requests.post(
        f"{BASE_URL}/auth/token",
        params={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
    )
    response.raise_for_status()
    data = response.json()

    _auth_state["token"] = data["access_token"]
    _auth_state["expires_at"] = time.time() + data["expires_in"] - 5
    print(f"[auth] novo token obtido, válido por {data['expires_in']}s")


def get_valid_token():
    """Devolve um token válido, pedindo um novo só se necessário."""
    if _auth_state["token"] is None or time.time() >= _auth_state["expires_at"]:
        _request_new_token()
    return _auth_state["token"]


# ---------------------------------------------------------------------------
# Chamada genérica com paginação + retry + refresh de token
# ---------------------------------------------------------------------------
def fetch_all(endpoint: str, extra_params: dict | None = None) -> list[dict]:
    """
    Busca TODOS os registros de um endpoint, percorrendo todas as páginas.
    Trata token vencido (401) e falha de servidor (500) com retry.
    """
    all_records = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        params = {"page": page, "page_size": PAGE_SIZE}
        if extra_params:
            params.update(extra_params)

        record_batch = None

        for attempt in range(1, MAX_RETRIES + 1):
            token = get_valid_token()
            headers = {"Authorization": f"Bearer {token}"}

            response = requests.get(f"{BASE_URL}/{endpoint}", params=params, headers=headers)

            if response.status_code == 200:
                record_batch = response.json()
                break

            if response.status_code == 401:
                print(f"[{endpoint}] token expirado no meio da extração, renovando...")
                _auth_state["token"] = None
                continue

            if response.status_code == 500:
                print(f"[{endpoint}] falha de servidor (tentativa {attempt}/{MAX_RETRIES}), "
                      f"tentando de novo em {RETRY_BACKOFF_SECONDS}s...")
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue

            response.raise_for_status()

        if record_batch is None:
            raise RuntimeError(
                f"[{endpoint}] falhou {MAX_RETRIES} vezes seguidas na página {page}, desistindo."
            )

        all_records.extend(record_batch["data"])
        total_pages = record_batch["pagination"]["total_pages"]
        print(f"[{endpoint}] página {page}/{total_pages} -> "
              f"{len(record_batch['data'])} registros")

        page += 1

    return all_records


# ---------------------------------------------------------------------------
# Orquestração da extração
# ---------------------------------------------------------------------------
def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    entities = ["customers", "products", "orders", "order_items"]

    for entity in entities:
        print(f"\n=== Extraindo {entity} ===")
        records = fetch_all(entity)

        df = pd.DataFrame(records)
        out_path = os.path.join(RAW_DIR, f"{entity}.csv")
        df.to_csv(out_path, index=False)

        print(f"[{entity}] {len(df)} registros salvos em {out_path}")


if __name__ == "__main__":
    main()