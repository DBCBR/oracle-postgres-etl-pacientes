import os
from pathlib import Path
from pathlib import Path
import sys

# Wrapper to import module from src
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from pg_client import insert_or_update_user

if __name__ == '__main__':
    print('This module is a wrapper. Use import insert_or_update_user from pg_client in src.')
        conn.close()
        print(f"[PG] Inserido/atualizado IdAdimission={record.get('IdAdimission')}")
        return True
    except Exception as e:
        print(f"[PG][ERRO] {e}")
        return False
