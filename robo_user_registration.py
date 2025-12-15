import os
import base64
from argon2 import low_level, Type

# ============================================================================
# CONFIGURAÇÃO DO ALGORITMO ARGON2ID
# ============================================================================
PARALLELISM = 8 
from pathlib import Path
import sys

# Wrapper to import module from src
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from robo_user_registration import gerar_senha_e_hash

if __name__ == '__main__':
    print('Use gerar_senha_e_hash from robo_user_registration in src')
    e gera o Hash e o Salt compatíveis com o sistema legado em C#.
