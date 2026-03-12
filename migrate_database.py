import sqlite3
import re
from db import ContratoDB, Contrato

SOURCE_DB = 'database.db'
TARGET_DB = 'contratos.db'

def migrate():
    try:
        src_conn = sqlite3.connect(SOURCE_DB)
    except Exception as e:
        print('Fonte não encontrada:', SOURCE_DB)
        return
    src_conn.row_factory = sqlite3.Row
    cur = src_conn.cursor()
    try:
        cur.execute('SELECT numero_contrato, cliente_nome, cliente_cpf, valor_contrato, data_assinatura FROM contratos')
        rows = cur.fetchall()
    except Exception as e:
        print('Erro ao ler tabela de origem:', e)
        return

    if not rows:
        print('Nenhum registro encontrado em', SOURCE_DB)
        return

    db = ContratoDB(TARGET_DB)
    count = 0
    for r in rows:
        numero = r['numero_contrato']
        cliente = r['cliente_nome']
        cpf_raw = r['cliente_cpf']
        cpf = re.sub(r"\D", "", cpf_raw or '')
        try:
            valor = float(r['valor_contrato'])
        except Exception:
            valor = 0.0
        data = r['data_assinatura']
        contrato = Contrato(id=None, numero=numero, cliente=cliente, cliente_cpf=cpf, valor=valor, data=data)
        try:
            db.insert(contrato)
            count += 1
        except Exception as e:
            print('Falha ao inserir:', numero, e)
    print(f'Migração concluída: {count} registros importados para {TARGET_DB}')

if __name__ == '__main__':
    migrate()
