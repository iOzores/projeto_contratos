import re


def parse_money_br(value):
    if value is None:
        raise ValueError("Valor inválido")
    s = str(value).strip()
    if s == "":
        raise ValueError("Valor inválido")

    s = s.replace("R$", "").replace("r$", "").replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    return float(s)


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")
