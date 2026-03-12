from flask import Flask, render_template, request, redirect, url_for, flash
from db import ContratoDB, Contrato
import sqlite3
import re
import os
import traceback

app = Flask(__name__)
app.secret_key = "dev-secret-for-flash-messages"


# Filtro para formatar valores como moeda brasileira: R$ 1.234,56
def _format_currency(value):
    try:
        v = float(value)
    except Exception:
        return value
    s = f"{v:,.2f}"  # 1,234.56
    # trocar separadores: 1,234.56 -> 1.234,56
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"


app.jinja_env.filters['currency'] = _format_currency


# Filtro para formatar CPF na apresentação: xxx.xxx.xxx-xx
def _format_cpf(value):
    import re
    if value is None:
        return ''
    s = re.sub(r"\D", "", str(value))
    if len(s) == 11:
        return f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}"
    return value

app.jinja_env.filters['cpf'] = _format_cpf

# Instância compartilhada do banco (cria tabela se necessário)
db_path = os.path.join(os.path.dirname(__file__), "contratos.db")
db = ContratoDB(db_path)

@app.route('/')
def index():
    # Não retornar os contratos cadastrados para que não apareçam na UI
    return render_template('index.html', contratos=None)


@app.route('/incluir', methods=['GET', 'POST'])
def incluir_contrato():
    # GET: mostra o formulário de inclusão
    if request.method == 'GET':
        # gerar um número para exibir no formulário (não garante reserva até o POST)
        try:
            numero_preview = db.generate_unique_numero()
        except Exception:
            numero_preview = ''
        return render_template('incluir.html', numero_preview=numero_preview)
    cliente = request.form.get('cliente')
    cpf = request.form.get('cpf')
    valor = request.form.get('valor')
    data = request.form.get('data')

    errors = []

    # valor
    try:
        valor_f = float(valor)
    except (TypeError, ValueError):
        errors.append("Valor inválido")
        valor_f = None

    # campos obrigatórios
    if not cliente or cliente.strip() == "":
        errors.append("Nome do cliente é obrigatório")
    # validar CPF (remover não dígitos e verificar 11 dígitos)
    cpf_digits = re.sub(r"\D", "", cpf or "")
    if not cpf or cpf.strip() == "":
        errors.append("CPF do cliente é obrigatório")
    elif len(cpf_digits) != 11:
        errors.append("CPF inválido. Deve conter 11 dígitos")
    if not data or data.strip() == "":
        errors.append("Data de assinatura é obrigatória")

    # O número do contrato é sempre gerado/confirmado pelo backend (formato xxxxx-xx)
    # Preferir o número enviado no form (previsão) se ainda estiver disponível.
    numero_form = request.form.get('numero')

    if errors:
        for e in errors:
            flash(e, 'error')
        return redirect(url_for('index'))

    # primeiro, tentar usar o número vindo do formulário (pré-gerado na exibição)
    attempts = 6
    last_err = None
    for attempt in range(attempts):
        if attempt == 0 and numero_form and db._valid_numero(numero_form) and not db.exists_numero(numero_form):
            numero_candidate = numero_form
        else:
            try:
                numero_candidate = db.generate_unique_numero()
            except Exception as e:
                last_err = e
                break

        contrato = Contrato(id=None, numero=numero_candidate, cliente=cliente, cliente_cpf=cpf_digits, valor=valor_f or 0.0, data=data)
        try:
            db.insert(contrato)
            last_err = None
            numero = numero_candidate
            break
        except sqlite3.IntegrityError as ie:
            # colisão no índice único - tentar novamente
            last_err = ie
            continue
        except ValueError as ve:
            # formato inválido (não deveria ocorrer para numeros gerados)
            last_err = ve
            break
        except Exception as e:
            last_err = e
            break

    if last_err is not None:
        traceback.print_exc()
        flash('Erro ao salvar o contrato: ' + str(last_err), 'error')
        return redirect(url_for('index'))

    flash('Contrato incluído com sucesso.', 'success')
    return redirect(url_for('consultar_contratos'))


@app.route('/consultar')
def consultar_contratos():
    # Página separada para consulta da base de contratos
    q = request.args.get('q', '')
    by = request.args.get('by', 'auto')
    if q and q.strip() != '':
        contratos = db.search(q, by=by)
    else:
        contratos = []
    return render_template('consultar.html', contratos=contratos)


@app.route('/excluir/<int:contrato_id>', methods=['POST'])
def excluir_contrato(contrato_id: int):
    try:
        db.delete(contrato_id)
    except Exception as e:
        traceback.print_exc()
        flash('Erro ao excluir contrato: ' + str(e), 'error')
    return redirect(url_for('index'))


@app.route('/editar/<int:contrato_id>', methods=['POST'])
def editar_contrato(contrato_id: int):
    numero = request.form.get('numero')
    cliente = request.form.get('cliente')
    cpf = request.form.get('cpf')
    valor = request.form.get('valor')
    data = request.form.get('data')

    try:
        valor_f = float(valor) if valor is not None and valor != "" else None
    except (TypeError, ValueError):
        valor_f = None

    updates = {}
    if numero is not None and numero != "":
        updates["numero"] = numero
    if cliente is not None and cliente != "":
        updates["cliente"] = cliente
    if cpf is not None and cpf != "":
        cpf_digits = re.sub(r"\D", "", cpf)
        if len(cpf_digits) != 11:
            flash('CPF inválido. Deve conter 11 dígitos', 'error')
            return redirect(url_for('index'))
        updates["cliente_cpf"] = cpf_digits
    if valor_f is not None:
        updates["valor"] = valor_f
    if data is not None and data != "":
        updates["data"] = data

    if updates:
        try:
            db.update(contrato_id, **updates)
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('index'))
        except Exception as e:
            traceback.print_exc()
            flash('Erro ao editar contrato: ' + str(e), 'error')
            return redirect(url_for('index'))

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)