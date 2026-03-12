from typing import Optional
from db import Contrato, ContratoDB


class IncluirContrato:
    """Classe responsável por incluir contratos no banco."""

    def __init__(self, db_path: Optional[str] = None):
        self.db = ContratoDB(db_path) if db_path else ContratoDB()

    def incluir(self, numero: str, cliente: str, cliente_cpf: str, valor: float, data: str) -> int:
        contrato = Contrato(id=None, numero=numero, cliente=cliente, cliente_cpf=cliente_cpf, valor=valor, data=data)
        return self.db.insert(contrato)

    def close(self) -> None:
        self.db.close()
