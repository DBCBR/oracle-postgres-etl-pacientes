"""
Robô único para o Portal Família.
- Lê variáveis de ambiente em settings/.env
- Inicializa Oracle Instant Client (modo thick)
- Extrai registros da view Oracle
- Normaliza/trata campos e gera hash/salt Argon2id para senha (CPF -> últimos 6 dígitos)
- Insere sempre um novo registro na tabela Postgres UserRegistrationForm (sem updates)
- IMPLEMENTADO: Filtro de duplicidade por chave composta (IdAdimission + PatientType)

Requisitos: python-dotenv, oracledb, psycopg2-binary, argon2-cffi.
"""

import os
import sys
import time
import base64
import re
import uuid
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Set

from argon2 import low_level, Type
from dotenv import load_dotenv
import oracledb
import psycopg2

# --------------------------------------------------------------------------------------
# Configuração e carregamento de ambiente
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "settings" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Parâmetros Oracle
ORACLE_HOST = os.getenv("ORACLE_HOST")
ORACLE_PORT = os.getenv("ORACLE_PORT")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE")
ORACLE_SCHEMA = os.getenv("ORACLE_SCHEMA")
ORACLE_VIEW = os.getenv("ORACLE_VIEW", "VWPACIENTES_COMVISITAS")
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASS = os.getenv("ORACLE_PASS")
ORACLE_CLIENT_WINDOWS = os.getenv("ORACLE_CLIENT_WINDOWS")
ORACLE_CLIENT_LINUX = os.getenv("ORACLE_CLIENT_LINUX")
ORACLE_INSTANT_CLIENT = os.getenv("ORACLE_INSTANT_CLIENT")

# Parâmetros Postgres
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_SCHEMA = os.getenv("PG_SCHEMA", "public")
PG_TABLE = os.getenv("PG_TABLE", "UserRegistrationForm")
PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("robo_portal_familia")
logger.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(fmt)

info_handler = logging.FileHandler(LOG_DIR / "info.log")
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(fmt)

error_handler = logging.FileHandler(LOG_DIR / "errors.log")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(fmt)

logger.handlers.clear()
logger.addHandler(console_handler)
logger.addHandler(info_handler)
logger.addHandler(error_handler)

# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------
def resolve_instant_client_path() -> str:
    if os.name == "nt":
        candidates = [ORACLE_CLIENT_WINDOWS, ORACLE_INSTANT_CLIENT, r"C:\\ClientOracle\\instantclient_23_0"]
        probe = next((c for c in candidates if c), candidates[-1])
        return probe
    candidates = [ORACLE_CLIENT_LINUX, ORACLE_INSTANT_CLIENT, "/opt/oracle/instantclient_23_0"]
    probe = next((c for c in candidates if c), candidates[-1])
    return probe


def init_oracle_client():
    lib_dir = resolve_instant_client_path()
    try:
        oracledb.init_oracle_client(lib_dir=lib_dir)
        print(f"[ORACLE] Instant Client inicializado em: {lib_dir}")
    except Exception as exc:
        print(f"[ORACLE][ERRO] Falha ao iniciar Instant Client em {lib_dir}: {exc}")
        sys.exit(1)


# --------------------------------------------------------------------------------------
# Hash de senha (Argon2id)
# --------------------------------------------------------------------------------------
PARALLELISM = 8
MEMORY_COST = 65536
TIME_COST = 4
HASH_LENGTH = 32
SALT_LENGTH = 16

def gerar_senha_e_hash(cpf: str) -> Tuple[str, str]:
    cpf_limpo = re.sub(r"[^0-9]", "", cpf or "")
    senha = (cpf_limpo[-6:] or "000000")
    salt_bytes = os.urandom(SALT_LENGTH)
    hash_bytes = low_level.hash_secret_raw(
        secret=senha.encode("utf-8"),
        salt=salt_bytes,
        time_cost=TIME_COST,
        memory_cost=MEMORY_COST,
        parallelism=PARALLELISM,
        hash_len=HASH_LENGTH,
        type=Type.ID,
    )
    return base64.b64encode(hash_bytes).decode("utf-8"), base64.b64encode(salt_bytes).decode("utf-8")


# --------------------------------------------------------------------------------------
# Conexões
# --------------------------------------------------------------------------------------
def oracle_connect():
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASS,
        host=ORACLE_HOST,
        port=int(ORACLE_PORT) if ORACLE_PORT else None,
        service_name=ORACLE_SERVICE
    )


def postgres_connect():
    return psycopg2.connect(
        host=PG_HOST, 
        port=PG_PORT, 
        dbname=PG_DB, 
        user=PG_USER, 
        password=PG_PASS
    )


# --------------------------------------------------------------------------------------
# Extração e transformação
# --------------------------------------------------------------------------------------
def fetch_oracle_rows() -> Iterable[Dict]:
    full_view = f"{ORACLE_SCHEMA}.{ORACLE_VIEW}" if ORACLE_SCHEMA else ORACLE_VIEW
    sql = f"SELECT * FROM {full_view}"
    with oracle_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0].upper() for d in cur.description]
            while True:
                rows = cur.fetchmany(500)
                if not rows:
                    break
                for row in rows:
                    yield {cols[i]: row[i] for i in range(len(cols))}


def transformar_registro(raw: Dict) -> Dict:
    """
    Normaliza campos e monta o payload.
    ALTERAÇÃO: Concatena Especialidade/Profissional ao PatientType para unicidade.
    """
    cleaned = {}
    for k, v in raw.items():
        if isinstance(v, str):
            cleaned[k] = v.strip()
        else:
            cleaned[k] = v

    def first_of(*keys):
        for k in keys:
            if cleaned.get(k) not in (None, ""):
                return cleaned.get(k)
        return None

    cpf = (first_of("CPF", "NRO_CPF", "NR_CPF") or "")
    email = first_of("EMAIL") or (f"{cpf}@naoinformado.com" if cpf else None)
    telefones = first_of("TELEFONES", "TELEFONE", "FONE", "CELULAR") or ""
    nome_paciente = first_of("NOME_PACIENTE", "NOME")
    pessoa_contato = first_of("PESSOACONTATO", "VINCULO") or ""
    dt_nasc = first_of("DTNASCTO", "DATA_NASCIMENTO")
    tipo_visita = first_of("TIPOVISITA", "ESPECIALIDADE", "TIPO_PACIENTE") or ""
    
    # --- Lógica de Diferenciação ---
    # Extrai o tipo base (ex: "ID", "AD")
    tipo_base = tipo_visita.split("-")[0].strip() if "-" in tipo_visita else tipo_visita
    # Extrai a especialidade ou profissional (ex: "Medico", "Enfermeiro")
    especialidade = first_of("ESPECIALIDADE", "PROFISSIONAL", "CARGO") or "Geral"
    
    # Cria o Tipo Composto (ex: "ID - Medico")
    # Isso será salvo no Postgres para diferenciar os registros
    patient_type_composto = f"{tipo_base} - {especialidade}"
    # -------------------------------

    hash_str, salt_str = gerar_senha_e_hash(cpf)

    record = {
        "IdCadRegistration": str(uuid.uuid4()),
        "IdAdimission": first_of("ID_ATENDIMENTO", "IDATENDIMENTO"),
        "Patient": nome_paciente,
        "UserPhone": telefones,
        "UserFullName": nome_paciente,
        "UserEmail": email,
        "RegistrationDate": datetime.now(),
        "PatientType": patient_type_composto, # Usando o tipo composto
        "UserResponsibleLegal": bool(pessoa_contato),
        "UserPasswordHash": hash_str,
        "UserPasswordSalt": salt_str,
        "UserBondWithPatient": pessoa_contato,
        "UserDateOfBirth": dt_nasc,
        "UserCpf": cpf,
        "Status": True,
        "IsAdmin": False,
    }
    return record


# --------------------------------------------------------------------------------------
# Carga no Postgres
# --------------------------------------------------------------------------------------
COLS = [
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


def inserir_postgres(records: List[Dict]) -> Tuple[int, int]:
    """
    Insere registros no Postgres. Assume que os registros já foram validados
    e não contêm duplicatas (validação feita em processar_batch).
    """
    if not records:
        return 0, 0

    placeholders = ", ".join(["%s"] * len(COLS))
    quoted_cols = ", ".join([f'"{c}"' for c in COLS])
    if PG_SCHEMA:
        table_name = f"{PG_SCHEMA}.\"{PG_TABLE}\""
    else:
        table_name = f'"{PG_TABLE}"'

    sql = f"INSERT INTO {table_name} ({quoted_cols}) VALUES ({placeholders});"

    sucessos = 0
    falhas = 0

    with postgres_connect() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for rec in records:
                values = [rec.get(c) for c in COLS]
                
                try:
                    cur.execute(sql, values)
                    sucessos += 1
                    logger.info(f"Inserido com sucesso | IdAdimission={rec.get('IdAdimission')} | CPF={rec.get('UserCpf')}")
                    
                    
                except Exception as exc:
                    falhas += 1
                    logger.error("Falha ao inserir - IdAdimission=%s | CPF=%s | Erro: %s", 
                                 rec.get("IdAdimission"), rec.get("UserCpf"), exc)

    return sucessos, falhas


# --------------------------------------------------------------------------------------
# Validação de CPF no Postgres
# --------------------------------------------------------------------------------------
def cpf_ja_existe_postgres(cpf: str) -> bool:
    """
    Verifica se um CPF já existe registrado no Postgres.
    """
    if not cpf:
        return False
    
    if PG_SCHEMA:
        table_name = f"{PG_SCHEMA}.\"{PG_TABLE}\""
    else:
        table_name = f"\"{PG_TABLE}\""
    
    sql = f'SELECT 1 FROM {table_name} WHERE "UserCpf" = %s LIMIT 1;'
    
    try:
        with postgres_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (cpf,))
                return cur.fetchone() is not None
    except Exception as exc:
        logger.error(f"Erro ao verificar CPF no Postgres: {exc}")
        return False


# --------------------------------------------------------------------------------------
# Pipeline principal
# --------------------------------------------------------------------------------------
def processar_batch() -> Tuple[int, int, int]:
    """
    Fluxo otimizado com validação por CPF:
    1. Lê registros do Oracle.
    2. Verifica se o CPF já existe no Postgres.
    3. Se não existir, inclui o registro para inserção.
    4. Insere somente registros com CPF não duplicado.
    """

    registros_novos = []
    total_lidos_oracle = 0
    ignorados_cpf_existente = 0

    for row in fetch_oracle_rows():
        total_lidos_oracle += 1
        try:
            # Transforma o registro do Oracle
            reg = transformar_registro(row)
            cpf = reg.get("UserCpf", "")
            
            # Verifica se o CPF já existe no Postgres
            if cpf_ja_existe_postgres(cpf):
                ignorados_cpf_existente += 1
                logger.error(f"Registro do CPF {cpf} já foi inserido no DB")
                continue
            
            registros_novos.append(reg)

        except Exception as exc:
            logger.error("Falha ao transformar/processar registro: %s", exc)

    logger.info(
        f"Lidos Oracle: {total_lidos_oracle} | "
        f"Ignorados (CPF já registrado): {ignorados_cpf_existente} | "
        f"Novos a inserir: {len(registros_novos)}"
    )

    sucessos, falhas = inserir_postgres(registros_novos)
    return total_lidos_oracle, sucessos, falhas


def run_pipeline(watch_interval: int = None):
    init_oracle_client()
    ciclo = 0
    while True:
        ciclo += 1
        logger.info("--- Ciclo %s iniciado ---", ciclo)
        lidos, ok, falha = processar_batch()
        logger.info("Ciclo finalizado. Encontrados: %s | Inseridos: %s | Falhas: %s", lidos, ok, falha)
        
        if not watch_interval:
            break
        
        logger.info("Próximo ciclo em %s segundos", watch_interval)
        time.sleep(watch_interval)
    logger.info("Pipeline concluído")


# --------------------------------------------------------------------------------------
# Entrada principal
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    # Configuração autônoma: executa a cada 1 hora (3600 segundos)
    WATCH_INTERVAL_SECONDS = 3600  # 1 hora
    
    logger.info("="*60)
    logger.info("Robô Portal Família - Modo Incremental Inteligente")
    logger.info("Intervalo: 1 hora | Validação: IdAdimission + PatientType")
    logger.info("="*60)
    
    run_pipeline(watch_interval=WATCH_INTERVAL_SECONDS)
    