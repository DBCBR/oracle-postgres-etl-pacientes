import time
import json
import db_local
import re
import argparse
import uuid
from datetime import datetime
from robo_user_registration import gerar_senha_e_hash
import pg_client


def run_loop(run_once: bool = False, sleep_interval: int = 10, preview: bool = False, max_count: int = None):
    print("--- INICIANDO PERFORMER (Robô de Cadastro) ---")
    db_local.inicializar_db()

    processed = 0
    errors = 0

    while True:
        if max_count is not None and processed >= max_count:
            print(f"Alcançado limite de processamento: {processed} registros. Encerrando.")
            break

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
            nome_paciente = dados_paciente.get('NOME_PACIENTE') or dados_paciente.get('NOME')
            pessoa_contato = dados_paciente.get('PESSOACONTATO') or ''
            dt_nasc = dados_paciente.get('DTNASCTO') or dados_paciente.get('DATA_NASCIMENTO')
            tipo_visita = (dados_paciente.get('TIPOVISITA') or '')
            patient_type = tipo_visita.split('-')[0].strip() if '-' in tipo_visita else tipo_visita

            tokens = [
                "pai","mãe","mae","filho","filha","irmão","irmao","irmã","irma","neto","neta",
                "sobrinho","sobrinha","cunhado","cunhada","marido","mulher","esposo","esposa",
                "genro","nora","cuidador","cuidadora","próprio","proprio","avô","avo",
            ]

            lower_contato = (pessoa_contato or '').lower()
            bond = 'mãe'
            for t in tokens:
                if re.search(r"\b" + re.escape(t) + r"\b", lower_contato):
                    bond = t
                    break

            hash_str, salt_str = gerar_senha_e_hash(cpf if cpf else '')

            record = {
                'IdCadRegistration': str(uuid.uuid4()),
                'IdAdimission': id_paciente,
                'Patient': nome_paciente,
                'UserPhone': telefones,
                'UserFullName': nome_paciente,
                'UserEmail': email,
                'RegistrationDate': datetime.now(),
                'PatientType': patient_type,
                'UserResponsibleLegal': True if pessoa_contato else False,
                'UserPasswordHash': hash_str,
                'UserPasswordSalt': salt_str,
                'UserBondWithPatient': pessoa_contato or bond,
                'UserDateOfBirth': dt_nasc,
                'UserCpf': cpf,
                'Status': True,
                'IsAdmin': False,
            }

            if preview:
                print('--- PREVIEW (não será enviado) ---')
                print(record)
                # do not mark as concluded; leave in queue for real run
                processed += 1
                continue

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
    parser.add_argument('--preview', action='store_true', help='Mostra o payload que seria enviado, sem gravar')
    parser.add_argument('--count', type=int, help='Quantidade máxima de registros a processar (ou visualizar)')
    args = parser.parse_args()
    run_loop(run_once=args.once, preview=args.preview, max_count=args.count)


if __name__ == '__main__':
    main()
