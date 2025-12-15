import time
import json
import db_local
import re
import argparse
from robo_user_registration import gerar_senha_e_hash
import pg_client


def run_loop(run_once: bool = False, sleep_interval: int = 10):
    print("--- INICIANDO PERFORMER (Robô de Cadastro) ---")
    db_local.inicializar_db()

    processed = 0
    errors = 0

    while True:
        tarefa = db_local.pegar_proximo_pendente()

        if not tarefa:
            if run_once:
                print("Fila vazia — modo once: encerrando.")
                break
            print(f"Zzz... Fila vazia. Aguardando {sleep_interval} segundos...")
            time.sleep(sleep_interval)
            continue

        id_paciente = tarefa['id_paciente']
        dados_paciente = json.loads(tarefa['dados_json'])

        print(f"Processando ID {id_paciente}...")

        try:
            cpf = (dados_paciente.get('CPF') or '').strip()
            email = dados_paciente.get('EMAIL') or (cpf + "@naoinformado.com" if cpf else None)
            telefones = dados_paciente.get('TELEFONES') or dados_paciente.get('TELEFONE') or ''
            nome_paciente = dados_paciente.get('NOME_PACIENTE')
            pessoa_contato = dados_paciente.get('PESSOACONTATO') or ''
            dt_nasc = dados_paciente.get('DTNASCTO')
            tipo_visita = (dados_paciente.get('TIPOVISITA') or '')
            patient_type = tipo_visita.split('-')[0].strip() if '-' in tipo_visita else tipo_visita

            tokens = [
                "pai","mãe","mae","filho","filha","irmão","irmao","irmã","irma","neto","neta",
                "sobrinho","sobrinha","cunhado","cunhada","marido","mulher","esposo","esposa",
                "genro","nora","cuidador","cuidadora","próprio","proprio","avô","avo",
            ]

            lower_contato = pessoa_contato.lower()
            bond = 'mãe'
            for t in tokens:
                if re.search(r"\b" + re.escape(t) + r"\b", lower_contato):
                    bond = t
                    break

            hash_str, salt_str = gerar_senha_e_hash(cpf if cpf else '')

            record = {
                'IdAdimission': id_paciente,
                'Patient': nome_paciente,
                'UserPhone': telefones,
                'UserFullName': pessoa_contato,
                'UserEmail': email,
                'PatientType': patient_type,
                'UserResponsibleLegal': True,
                'UserPasswordHash': hash_str,
                'UserPasswordSalt': salt_str,
                'UserBondWithPatient': bond,
                'UserDateOfBirth': dt_nasc,
                'UserCpf': cpf,
                'Status': True,
                'IsAdmin': False,
            }

            sucesso = pg_client.insert_or_update_user(record)
            db_local.marcar_concluido(id_paciente, sucesso=sucesso)

            if sucesso:
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
