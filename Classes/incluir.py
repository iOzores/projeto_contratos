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

    def validar_entrada(self, cliente: str, cpf: str, valor: str, data: str, taxa_juros: str = None, data_nascimento: str = None, prazo_meses: str = None, sistema_amortizacao: str = None):
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

        taxa_f = 0.0
        if taxa_juros is not None and (str(taxa_juros).strip() != ""):
            try:
                taxa_f = parse_money_br(taxa_juros)
            except Exception:
                errors.append("Taxa de juros inválida")

        data_nasc_val = None
        if data_nascimento is not None and (str(data_nascimento).strip() != ""):
            data_nasc_val = data_nascimento.strip()

        prazo_val = 12
        if prazo_meses is not None and (str(prazo_meses).strip() != ""):
            try:
                prazo_val = int(str(prazo_meses).strip())
                if prazo_val <= 0:
                    raise ValueError()
            except Exception:
                errors.append("Prazo do contrato inválido")
                prazo_val = 12

        sistema_val = (sistema_amortizacao or "").strip().upper()
        if sistema_val and sistema_val not in {"SAC", "PRICE"}:
            errors.append("Sistema de amortização inválido")
            sistema_val = ""

        payload = {
            "cliente": cliente_limpo,
            "cliente_cpf": cpf_digits,
            "valor": valor_f,
            "data": data_limpa,
            "taxa_juros": taxa_f,
            "data_nascimento": data_nasc_val,
            "prazo_meses": prazo_val,
            "sistema_amortizacao": sistema_val or None,
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
                prazo_meses=payload.get("prazo_meses", 12) or 12,
                taxa_juros=payload.get("taxa_juros", 0.0) or 0.0,
                data_nascimento=payload.get("data_nascimento"),
                data=payload["data"],
                sistema_amortizacao=payload.get("sistema_amortizacao"),
            )

            try:
                contrato_id = self.db.insert(contrato)
                return True, None, contrato_id
            except DuplicateNumeroError as e:
                last_err = e
                continue
            except ValueError as e:
                last_err = e
                break
            except Exception as e:
                last_err = e
                break

        return False, last_err, None
