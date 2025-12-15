import oracledb
import sys
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "settings" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def _resolve_instant_client_path():
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

try:
    oracledb.init_oracle_client(lib_dir=INSTANT_CLIENT_PATH)
    print(f"Modo Thick Oracle inicializado.")
except oracledb.Error as e:
    print(f"Erro ao inicializar o Instant Client: {e}")
    sys.exit(1)

ORACLE_HOST = os.getenv("ORACLE_HOST")
ORACLE_PORT = os.getenv("ORACLE_PORT")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE") 
ORACLE_SCHEMA = os.getenv("ORACLE_SCHEMA")
ORACLE_VIEW = os.getenv("ORACLE_VIEW")
ORACLE_USER = os.getenv("ORACLE_USER") 
ORACLE_PASS = os.getenv("ORACLE_PASS")

dsn = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"

connection = None

try:
    connection = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=dsn)
    print("Conexão com o Oracle (dbprod) estabelecida com sucesso!")
    full_view_name = f"{ORACLE_SCHEMA}.{ORACLE_VIEW}"
    query = f"SELECT * FROM {full_view_name}"
    print(f"Executando consulta e gerando DataFrame: {full_view_name}")
    df = pd.read_sql(query, connection)
    df = df.drop(columns=['EMAIL', 'PROFISSIONAL'], errors='ignore')
    print(f"Total de registros carregados: {len(df)}")
    print("Primeiras linhas do DataFrame:")
    print(df.head())
    for index, linha in df.iterrows():
        pass

except oracledb.Error as e:
    error_obj, = e.args
    print(f"Erro no Oracle DB: Código={error_obj.code}, Mensagem='{error_obj.message}'")
    sys.exit(1)

except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")

finally:
    if connection:
        connection.close()
    print("Conexão com o banco de dados Oracle fechada.")
