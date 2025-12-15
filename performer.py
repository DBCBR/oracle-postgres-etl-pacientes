import time
import json
import db_local
import re
import argparse
from robo_user_registration import gerar_senha_e_hash
from pathlib import Path
import sys

# Wrapper to import module from src
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from performer import main

if __name__ == "__main__":
    main()
                print("   [SUCESSO] Paciente cadastrado/atualizado no Postgres e marcado como concluído.")
                processed += 1
            else:
                print("   [FALHA] Marcado como erro no banco local.")
                errors += 1

        except Exception as e:
            print(f"   [ERRO FATAL] {e}")
            db_local.marcar_concluido(id_paciente, sucesso=False)
            errors += 1

    print(f"Processamento finalizado. Processados: {processed}, Erros: {errors}")


def main():
    parser = argparse.ArgumentParser(description='Performer - consome fila local e insere no Postgres')
    parser.add_argument('--once', action='store_true', help='Processa a fila atual e encerra')
    args = parser.parse_args()
    run_loop(run_once=args.once)


if __name__ == '__main__':
    main()

if __name__ == "__main__":
    main()