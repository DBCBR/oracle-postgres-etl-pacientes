import os
import base64
from argon2 import low_level, Type

PARALLELISM = 8 
MEMORY_COST = 65536 
TIME_COST = 4 
HASH_LENGTH = 32 
SALT_LENGTH = 16 


def gerar_senha_e_hash(cpf_usuario):
    cpf_limpo = cpf_usuario.replace(".", "").replace("-", "")
    senha_texto = cpf_limpo[-6:]

    salt_bytes = os.urandom(SALT_LENGTH)
    salt_string = base64.b64encode(salt_bytes).decode('utf-8')

    hash_bytes = low_level.hash_secret_raw(
        secret=senha_texto.encode('utf-8'),
        salt=salt_bytes,
        time_cost=TIME_COST,
        memory_cost=MEMORY_COST,
        parallelism=PARALLELISM,
        hash_len=HASH_LENGTH,
        type=Type.ID
    )

    hash_string = base64.b64encode(hash_bytes).decode('utf-8')

    return hash_string, salt_string


if __name__ == '__main__':
    cpf_exemplo = "111.493.177-28"
    try:
        hash_final, salt_final = gerar_senha_e_hash(cpf_exemplo)
        print("-" * 30)
        print("RESULTADOS PARA O BANCO DE DADOS:")
        print("-" * 30)
        print(f"UserPasswordHash: {hash_final}")
        print(f"UserPasswordSalt: {salt_final}")
        print("-" * 30)
    except Exception as e:
        print(f"Erro ao gerar hash: {e}")
