import oracledb
import sys
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import db_local

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "settings" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def _resolve_instant_client_path():
    """Seleciona o Instant Client adequado para o SO ou usa fallback legado."""
    env_var = "ORACLE_CLIENT_WINDOWS" if os.name == "nt" else "ORACLE_CLIENT_LINUX"
    candidate = os.getenv(env_var) or os.getenv("ORACLE_INSTANT_CLIENT") or r"C:\ClientOracle\instantclient_23_0"
    cand_path = Path(candidate)
    if cand_path.exists() and (cand_path / 'oci.dll').exists():
        return str(cand_path)
    if cand_path.exists() and cand_path.is_dir():
        for child in cand_path.iterdir():
            if child.is_dir() and child.name.startswith('instantclient') and (child / 'oci.dll').exists():
                return str(child)
    return str(cand_path)


INSTANT_CLIENT_PATH = _resolve_instant_client_path()
SQL_QUERY = """
SELECT vc.* FROM DBIWSOLARCUIDADOS.VWPACIENTES_COMVISITAS vc
"""

def main():
    print("--- INICIANDO DISPATCHER ---")
    db_local.inicializar_db()

    try:
        oracledb.init_oracle_client(lib_dir=INSTANT_CLIENT_PATH)
        print(f"Instant Client inicializado a partir de: {INSTANT_CLIENT_PATH}")
    except Exception as e:
        print(f"Falha ao inicializar Instant Client em {INSTANT_CLIENT_PATH}: {e}")
        print("Verifique se o Instant Client está instalado nesse caminho e se as dependências (Visual C++ Redistributable) estão presentes.")
        sys.exit(1)

    connection = None
    try:
        dsn = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE')}"
        connection = oracledb.connect(user=os.getenv('ORACLE_USER'), password=os.getenv('ORACLE_PASS'), dsn=dsn)
        df = pd.read_sql(SQL_QUERY, connection)
        df.columns = [col.upper() for col in df.columns]

        print("\n[DEBUG] Colunas encontradas no DataFrame:")
        print(df.columns.tolist())
        print("-" * 30)

        df = df.drop(columns=['EMAIL', 'PROFISSIONAL'], errors='ignore')

        print(f" > Total registros retornados: {len(df)}")

        novos = 0
        for index, linha in df.iterrows():
            dados_dict = linha.to_dict()
            id_p = dados_dict.get('ID_ATENDIMENTO') 
            nome_p = dados_dict.get('NOME_PACIENTE')
            if id_p is None and index == 0:
                 print(f"[ALERTA] ID é None! Colunas na linha: {dados_dict.keys()}")
            if id_p:
                if db_local.adicionar_paciente(id_p, nome_p, dados_dict):
                    novos += 1

        print(f"--- FIM. Novos pacientes na fila: {novos} ---")

    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
