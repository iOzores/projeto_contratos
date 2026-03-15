from .utils import only_digits, parse_money_br
from db import ContratoDB


class EditarContratoService:
    """Responsável pela edição de contratos bancários."""

    def __init__(self, db=None):
        self.db = db or ContratoDB()

    def preparar_updates(self, numero=None, cliente=None, cpf=None, valor=None, data=None):
        updates = {}

        if numero is not None and numero != "":
            updates["numero"] = numero
        if cliente is not None and cliente != "":
            updates["cliente"] = cliente
        if cpf is not None and cpf != "":
            cpf_digits = only_digits(cpf)
            if len(cpf_digits) != 11:
                return None, "CPF inválido. Deve conter 11 dígitos"
            updates["cliente_cpf"] = cpf_digits
        if valor is not None and valor != "":
            try:
                updates["valor"] = parse_money_br(valor)
            except Exception:
                return None, "Valor inválido"
        if data is not None and data != "":
            updates["data"] = data

        return updates, None

    def editar(self, contrato_id: int, updates: dict):
        if not updates:
            return True, None
        try:
            self.db.update(contrato_id, **updates)
            return True, None
        except Exception as e:
            return False, e
