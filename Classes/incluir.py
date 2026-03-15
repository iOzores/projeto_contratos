from db import ContratoDB, Contrato, DuplicateNumeroError
from .utils import only_digits, parse_money_br


class IncluirContratoService:
    """Responsável pela inclusão de contratos bancários."""

    def __init__(self, db=None):
        self.db = db or ContratoDB()

    def gerar_numero_preview(self) -> str:
        try:
            return self.db.generate_unique_numero()
        except Exception:
            return ""

    def validar_entrada(self, cliente: str, cpf: str, valor: str, data: str):
        errors = []

        try:
            valor_f = parse_money_br(valor)
        except Exception:
            errors.append("Valor inválido")
            valor_f = None

        cliente_limpo = (cliente or "").strip()
        data_limpa = (data or "").strip()
        cpf_digits = only_digits(cpf)

        if cliente_limpo == "":
            errors.append("Nome do cliente é obrigatório")
        if (cpf or "").strip() == "":
            errors.append("CPF do cliente é obrigatório")
        elif len(cpf_digits) != 11:
            errors.append("CPF inválido. Deve conter 11 dígitos")
        if data_limpa == "":
            errors.append("Data de assinatura é obrigatória")

        payload = {
            "cliente": cliente_limpo,
            "cliente_cpf": cpf_digits,
            "valor": valor_f,
            "data": data_limpa,
        }
        return errors, payload

    def salvar(self, payload: dict, numero_form: str = ""):
        attempts = 6
        last_err = None

        for attempt in range(attempts):
            if (
                attempt == 0
                and numero_form
                and self.db._valid_numero(numero_form)
                and not self.db.exists_numero(numero_form)
            ):
                numero_candidate = numero_form
            else:
                try:
                    numero_candidate = self.db.generate_unique_numero()
                except Exception as e:
                    last_err = e
                    break

            contrato = Contrato(
                id=None,
                numero=numero_candidate,
                cliente=payload["cliente"],
                cliente_cpf=payload["cliente_cpf"],
                valor=payload["valor"] or 0.0,
                data=payload["data"],
            )

            try:
                self.db.insert(contrato)
                return True, None
            except DuplicateNumeroError as e:
                last_err = e
                continue
            except ValueError as e:
                last_err = e
                break
            except Exception as e:
                last_err = e
                break

        return False, last_err
