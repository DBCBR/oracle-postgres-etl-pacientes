import sqlite3
import json

ARQUIVO_DB = "fila_pacientes.db"

def inicializar_db():
    """Cria a tabela local se não existir."""
    conn = sqlite3.connect(ARQUIVO_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fila_trabalho (
            id_paciente TEXT PRIMARY KEY,
            nome_paciente TEXT,
            dados_json TEXT,
            status TEXT DEFAULT 'PENDENTE',
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_processamento DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def adicionar_paciente(id_paciente, nome, dados_dict):
    """
    Tenta inserir um paciente. 
    Se o ID já existir (INSERT OR IGNORE), ele não duplica e retorna False.
    Retorna True se foi um novo paciente inserido.
    """
    conn = sqlite3.connect(ARQUIVO_DB)
    cursor = conn.cursor()
    
    # Converte dicionário com datas para texto JSON
    dados_json = json.dumps(dados_dict, default=str) 
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO fila_trabalho (id_paciente, nome_paciente, dados_json)
            VALUES (?, ?, ?)
        ''', (str(id_paciente), nome, dados_json))
        conn.commit()
        return cursor.rowcount > 0 # Retorna True se inseriu linha nova
    finally:
        conn.close()

def pegar_proximo_pendente():
    """Pega o próximo item da fila que ainda não foi processado."""
    conn = sqlite3.connect(ARQUIVO_DB)
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM fila_trabalho WHERE status = 'PENDENTE' LIMIT 1")
    item = cursor.fetchone()
    conn.close()
    return item

def marcar_concluido(id_paciente, sucesso=True):
    """Atualiza o status do paciente após o robô tentar cadastrar."""
    conn = sqlite3.connect(ARQUIVO_DB)
    cursor = conn.cursor()
    
    novo_status = 'CONCLUIDO' if sucesso else 'ERRO'
    
    cursor.execute('''
        UPDATE fila_trabalho 
        SET status = ?, data_processamento = CURRENT_TIMESTAMP 
        WHERE id_paciente = ?
    ''', (novo_status, str(id_paciente)))
    conn.commit()
    conn.close()
