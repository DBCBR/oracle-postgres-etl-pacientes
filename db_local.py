from pathlib import Path
import sys

# Wrapper to import module from src
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from db_local import inicializar_db, adicionar_paciente, pegar_proximo_pendente, marcar_concluido

if __name__ == '__main__':
    print('This module is a wrapper. Use functions from src/db_local.py')