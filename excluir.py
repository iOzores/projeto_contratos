from typing import Optional
from db import ContratoDB


class ExcluirContrato:
    """Classe responsável por excluir contratos no banco."""

    def __init__(self, db_path: Optional[str] = None):
        self.db = ContratoDB(db_path) if db_path else ContratoDB()

    def excluir(self, contrato_id: int) -> bool:
        return self.db.delete(contrato_id)

    def close(self) -> None:
        self.db.close()
