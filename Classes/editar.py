from typing import Optional
from db import ContratoDB


class EditarContrato:
    """Classe responsável por editar contratos no banco."""

    def __init__(self, db_path: Optional[str] = None):
        self.db = ContratoDB(db_path) if db_path else ContratoDB()

    def editar(self, contrato_id: int, numero: Optional[str] = None, cliente: Optional[str] = None, valor: Optional[float] = None, data: Optional[str] = None) -> bool:
        updates = {}
        if numero is not None:
            updates["numero"] = numero
        if cliente is not None:
            updates["cliente"] = cliente
        if valor is not None:
            updates["valor"] = valor
        if data is not None:
            updates["data"] = data
        return self.db.update(contrato_id, **updates)

    def close(self) -> None:
        self.db.close()
