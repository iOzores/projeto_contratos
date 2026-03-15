import random
from datetime import date, timedelta

from db import Contrato, ContratoDB, DuplicateNumeroError


PRIMEIROS_NOMES = [
    "Ana",
    "Bruno",
    "Carla",
    "Diego",
    "Eduarda",
    "Felipe",
    "Gabriela",
    "Henrique",
    "Isabela",
    "Joao",
    "Karina",
    "Lucas",
    "Mariana",
    "Nicolas",
    "Patricia",
    "Rafael",
    "Sofia",
    "Thiago",
    "Vanessa",
    "Yasmin",
    "Aline",
    "Caio",
    "Daniela",
    "Enzo",
    "Fernanda",
    "Gustavo",
    "Helena",
    "Igor",
    "Julia",
    "Leonardo",
    "Manuela",
    "Otavio",
]

SOBRENOMES = [
    "Souza",
    "Lima",
    "Mendes",
    "Santos",
    "Rocha",
    "Costa",
    "Alves",
    "Martins",
    "Fernandes",
    "Ribeiro",
    "Gomes",
    "Araujo",
    "Nunes",
    "Oliveira",
    "Silva",
    "Teixeira",
    "Barros",
    "Cardoso",
    "Freitas",
    "Duarte",
    "Pereira",
    "Batista",
    "Moura",
    "Rezende",
    "Vieira",
    "Pinto",
    "Camargo",
    "Farias",
    "Correia",
    "Andrade",
    "Moreira",
    "Monteiro",
]


def random_unique_names(total: int) -> list[str]:
    combinations = [f"{first} {last}" for first in PRIMEIROS_NOMES for last in SOBRENOMES]
    if total > len(combinations):
        raise ValueError("Quantidade solicitada de nomes excede combinações disponíveis")
    return random.sample(combinations, total)


def random_cpf() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(11))


def random_date() -> str:
    start = date(2020, 1, 1)
    end = date.today()
    delta_days = (end - start).days
    picked = start + timedelta(days=random.randint(0, delta_days))
    return picked.isoformat()


def random_valor() -> float:
    return round(random.uniform(1000.0, 150000.0), 2)


def seed_contracts(total: int = 100) -> None:
    try:
        db = ContratoDB(table_name="contratos_bancarios")
    except Exception as e:
        print("Falha ao conectar no PostgreSQL.")
        print("Verifique PGHOST, PGPORT, PGDATABASE, PGUSER e PGPASSWORD.")
        print(f"Detalhe: {e}")
        return

    conn_info = db.connection_info
    print(
        "Conectado em:",
        f"host={conn_info.get('host')} port={conn_info.get('port')} ",
        f"database={conn_info.get('database')} user={conn_info.get('user')}",
    )
    print("Tabela alvo: contratos_bancarios")

    nomes_unicos = random_unique_names(total)
    inserted = 0

    while inserted < total:
        numero = db.generate_unique_numero()
        contrato = Contrato(
            id=None,
            numero=numero,
            cliente=nomes_unicos[inserted],
            cliente_cpf=random_cpf(),
            valor=random_valor(),
            data=random_date(),
        )

        try:
            db.insert(contrato)
            inserted += 1
        except DuplicateNumeroError:
            continue

    total_rows = len(db.read_all())
    db.close()
    print(f"Inseridos nesta execucao: {inserted}")
    print(f"Total atual na tabela contratos_bancarios: {total_rows}")


if __name__ == "__main__":
    seed_contracts(100)
