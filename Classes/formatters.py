from datetime import datetime
import re


def format_currency(value):
    try:
        v = float(value)
    except Exception:
        return value
    s = f"{v:,.2f}"  # 1,234.56
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"


def format_decimal_br(value):
    try:
        v = float(value)
    except Exception:
        return value
    s = f"{v:,.2f}"  # 1,234.56
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def format_cpf(value):
    if value is None:
        return ''
    s = re.sub(r"\D", "", str(value))
    if len(s) == 11:
        return f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}"
    return value


def format_date_br(value):
    if value is None:
        return ''
    s = str(value).strip()
    if s == '':
        return ''

    try:
        if len(s) >= 10 and s[4] == '-' and s[7] == '-':
            return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        pass

    return value


def register_jinja_filters(app):
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['decimal_br'] = format_decimal_br
    app.jinja_env.filters['cpf'] = format_cpf
    app.jinja_env.filters['date_br'] = format_date_br
