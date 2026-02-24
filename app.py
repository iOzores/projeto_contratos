from flask import Flask, render_template, request, redirect, url_for
from db import ContratoDB, Contrato

app = Flask(__name__)

# Instância compartilhada do banco (cria tabela se necessário)
db = ContratoDB("contratos.db")


@app.route('/')
def index():
    contratos = db.read_all()
    return render_template('index.html', contratos=contratos)


@app.route('/incluir', methods=['POST'])
def incluir_contrato():
    numero = request.form.get('numero')
    cliente = request.form.get('cliente')
    valor = request.form.get('valor')
    data = request.form.get('data')

    try:
        valor_f = float(valor)
    except (TypeError, ValueError):
        valor_f = 0.0

    contrato = Contrato(id=None, numero=numero or "", cliente=cliente or "", valor=valor_f, data=data or "")
    try:
        db.insert(contrato)
    except ValueError as e:
        return str(e), 400

    return redirect(url_for('index'))


@app.route('/excluir/<int:contrato_id>', methods=['POST'])
def excluir_contrato(contrato_id: int):
    db.delete(contrato_id)
    return redirect(url_for('index'))


@app.route('/editar/<int:contrato_id>', methods=['POST'])
def editar_contrato(contrato_id: int):
    numero = request.form.get('numero')
    cliente = request.form.get('cliente')
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
    if valor_f is not None:
        updates["valor"] = valor_f
    if data is not None and data != "":
        updates["data"] = data

    if updates:
        try:
            db.update(contrato_id, **updates)
        except ValueError as e:
            return str(e), 400

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)