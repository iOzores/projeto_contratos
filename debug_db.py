from db import ContratoDB

if __name__ == '__main__':
    db = ContratoDB('contratos.db')
    allc = db.read_all()
    print('TOTAL CONTRATOS:', len(allc))
    for i,c in enumerate(allc[:20], start=1):
        print(i, c)
    # try some heuristic searches based on data
    if allc:
        sample = allc[0]
        print('\n--- Testes de busca usando o primeiro registro ---')
        print('Buscar por nome (auto):', db.search(sample.cliente, by='auto'))
        print('Buscar por nome (nome):', db.search(sample.cliente, by='nome'))
        print('Buscar por cpf (cpf):', db.search(sample.cliente_cpf, by='cpf'))
        print('Buscar por numero (numero):', db.search(sample.numero, by='numero'))
    else:
        print('Base vazia - nenhuma busca será testada')
