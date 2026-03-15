from db import ContratoDB


class ConsultarContratoService:
    """Responsável pela consulta de contratos bancários."""

    def __init__(self, db=None):
        self.db = db or ContratoDB()

    def consultar(self, q: str, by: str = "auto"):
        if q and q.strip() != "":
            return self.db.search(q, by=by)
        return []
