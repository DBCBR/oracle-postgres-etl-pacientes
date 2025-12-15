import os
import base64
from argon2 import low_level, Type

# ============================================================================
# CONFIGURAÇÃO DO ALGORITMO ARGON2ID
# ============================================================================
# C#: argon2.DegreeOfParallelism = 8;
PARALLELISM = 8 
# C#: argon2.MemorySize = 65536; (64 MB)
MEMORY_COST = 65536 
# C#: argon2.Iterations = 4;
TIME_COST = 4 
# C#: argon2.GetBytes(32);
HASH_LENGTH = 32 
# C#: RandomNumberGenerator.GetBytes(16);
SALT_LENGTH = 16 

def gerar_senha_e_hash(cpf_usuario):
    """
    Recebe o CPF, pega os últimos 6 dígitos como senha,
    e gera o Hash e o Salt compatíveis com o sistema legado em C#.
    """
    
    # 1. REGRA DE NEGÓCIO: Senha = últimos 6 dígitos do CPF
    # Remove caracteres não numéricos para garantir segurança
    cpf_limpo = cpf_usuario.replace(".", "").replace("-", "")
    senha_texto = cpf_limpo[-6:]
    
    print(f"1. CPF original: {cpf_usuario}")
    print(f"2. Senha definida (últimos 6): {senha_texto}")

    # ---------------------------------------------------------
    # PASSO 1 (do e-mail): Gerar o salt
    # ---------------------------------------------------------
    # C#: byte[] saltBytes = RandomNumberGenerator.GetBytes(16);
    salt_bytes = os.urandom(SALT_LENGTH)
    
    # C#: string salt = Convert.ToBase64String(saltBytes);
    salt_string = base64.b64encode(salt_bytes).decode('utf-8')

    # ---------------------------------------------------------
    # PASSO 2 (do e-mail): Gerar o hash
    # ---------------------------------------------------------
    # Aqui usamos a função 'low_level' para ter controle total dos parâmetros
    hash_bytes = low_level.hash_secret_raw(
        secret=senha_texto.encode('utf-8'),
        salt=salt_bytes,
        time_cost=TIME_COST,
        memory_cost=MEMORY_COST,
        parallelism=PARALLELISM,
        hash_len=HASH_LENGTH,
        type=Type.ID # Equivalente a 'new Argon2id'
    )

    # C#: return Convert.ToBase64String(hashBytes);
    hash_string = base64.b64encode(hash_bytes).decode('utf-8')

    return hash_string, salt_string

# ============================================================================
# TESTANDO COM O CPF DO EXEMPLO
# ============================================================================
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