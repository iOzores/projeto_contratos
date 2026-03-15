from db import ContratoDB


class ExcluirContratoService:
    """Responsável pela exclusão de contratos bancários."""

    def __init__(self, db=None):
        self.db = db or ContratoDB()

    def excluir(self, contrato_id: int):
        return self.db.delete(contrato_id)
