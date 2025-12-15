import oracledb
import sys
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import db_local 

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "settings" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def _resolve_instant_client_path():
    """Seleciona o Instant Client adequado para o SO ou usa fallback legado."""
    env_var = "ORACLE_CLIENT_WINDOWS" if os.name == "nt" else "ORACLE_CLIENT_LINUX"
    candidate = os.getenv(env_var) or os.getenv("ORACLE_INSTANT_CLIENT") or r"C:\ClientOracle\instantclient_23_0"
    # Se o caminho já contém o oci.dll, use-o
    cand_path = Path(candidate)
    if cand_path.exists() and (cand_path / 'oci.dll').exists():
        return str(cand_path)

    # Se for um diretório que não contém oci.dll, procurar por subpastas instantclient_*
    if cand_path.exists() and cand_path.is_dir():
        from pathlib import Path
        import sys

        # Wrapper to import module from src
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
        from dispatcher import main

        if __name__ == "__main__":
            main()