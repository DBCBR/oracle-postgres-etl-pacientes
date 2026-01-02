import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "settings" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")
PG_TABLE = os.getenv("PG_TABLE", "UserRegistrationForm")
PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
DRY_RUN = os.getenv("DRY_RUN", "1")


def _get_conn():
    return psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)


def insert_or_update_user(record: dict) -> bool:
    if DRY_RUN and DRY_RUN != "0":
        print("[DRY_RUN] Payload para Postgres:")
        print(record)
        return True

    cols = [
        "IdCadRegistration",
        "IdAdimission",
        "Patient",
        "UserPhone",
        "UserFullName",
        "UserEmail",
        "RegistrationDate",
        "PatientType",
        "UserResponsibleLegal",
        "UserPasswordHash",
        "UserPasswordSalt",
        "UserBondWithPatient",
        "UserDateOfBirth",
        "UserCpf",
        "Status",
        "IsAdmin",
    ]

    values = [record.get(c) for c in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    # Usar identificadores entre aspas para preservar o casing exato das colunas
    quoted_cols = ", ".join([f'\"{c}\"' for c in cols])
    if PG_SCHEMA:
        qualified_table = f"{PG_SCHEMA}.\"{PG_TABLE}\""
    else:
        qualified_table = f"\"{PG_TABLE}\""

    # Sempre inserir um novo registro. Não usar ON CONFLICT para permitir múltiplas linhas
    sql = f"INSERT INTO {qualified_table} ({quoted_cols}) VALUES ({placeholders});"

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        cur.close()
        conn.close()
        print(f"[PG] Inserido/atualizado IdAdimission={record.get('IdAdimission')}")
        return True
    except Exception as e:
        print(f"[PG][ERRO] {e}")
        return False
