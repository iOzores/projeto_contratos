import sqlite3
import random
from datetime import datetime, timedelta

def gerar_cpf():
    return f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"

def gerar_numero_contrato():
    return f"{random.randint(10000, 99999)}-{random.randint(10, 99)}"

def popular_banco():
    # Conecta (ou cria) o banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Criando a tabela conforme sua especificação
    cursor.execute('DROP TABLE IF EXISTS contratos')
    cursor.execute('''
        CREATE TABLE contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_contrato TEXT NOT NULL,
            cliente_nome TEXT NOT NULL,
            cliente_cpf TEXT NOT NULL,
            valor_contrato REAL NOT NULL,
            taxa_juros REAL NOT NULL,
            data_assinatura TEXT NOT NULL
        )
    ''')

    # Listas para gerar nomes aleatórios
    nomes = ["João", "Maria", "José", "Ana", "Carlos", "Paula", "Lucas", "Juliana", "Ricardo", "Fernanda"]
    sobrenomes = ["Silva", "Oliveira", "Santos", "Souza", "Costa", "Pereira", "Almeida", "Nascimento"]

    dados = []
    data_inicial = datetime(2023, 1, 1)

    for _ in range(100):
        n_contrato = gerar_numero_contrato()
        nome_completo = f"{random.choice(nomes)} {random.choice(sobrenomes)} {random.choice(sobrenomes)}"
        cpf = gerar_cpf()
        valor = round(random.uniform(500.0, 100000.0), 2)
        # Taxa de juros com 1 dígito decimal (ex: 1.5, 2.9)
        taxa = round(random.uniform(0.5, 5.0), 1)
        data = (data_inicial + timedelta(days=random.randint(0, 700))).strftime('%Y-%m-%d')
        
        dados.append((n_contrato, nome_completo, cpf, valor, taxa, data))

    # Inserção em massa (Bulk Insert)
    cursor.executemany('''
        INSERT INTO contratos (numero_contrato, cliente_nome, cliente_cpf, valor_contrato, taxa_juros, data_assinatura) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', dados)

    conn.commit()
    conn.close()
    print("✓ Arquivo 'database.db' gerado com 100 registros!")

if __name__ == '__main__':
    popular_banco()