import re


def parse_money_br(value):
    if value is None:
        raise ValueError("Valor inválido")
    s = str(value).strip()
    if s == "":
        raise ValueError("Valor inválido")

    s = s.replace("R$", "").replace("r$", "").replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    return float(s)


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")
