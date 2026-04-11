from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
from db import ContratoDB
from Classes import (
    IncluirContratoService,
    ConsultarContratoService,
    EditarContratoService,
    ExcluirContratoService,
)
from Classes.formatters import register_jinja_filters
import traceback

app = Flask(__name__)
app.secret_key = "dev-secret-for-flash-messages"
register_jinja_filters(app)

# Instância compartilhada do banco (cria tabela se necessário)
db = ContratoDB()
incluir_service = IncluirContratoService(db)
consultar_service = ConsultarContratoService(db)
editar_service = EditarContratoService(db)
excluir_service = ExcluirContratoService(db)

@app.route('/')
def index():
    # Não retornar os registros de `contratos_bancarios` para não listar na home
    return render_template('index.html', contratos=None)


@app.route('/incluir', methods=['GET', 'POST'])
def incluir_contrato():
    # GET: mostra o formulário de inclusão
    if request.method == 'GET':
        numero_preview = incluir_service.gerar_numero_preview()
        return render_template('incluir.html', numero_preview=numero_preview)

    cliente = (request.form.get('cliente') or '').strip()
    cpf = (request.form.get('cpf') or '').strip()
    valor = (request.form.get('valor') or '').strip()
    data = (request.form.get('data') or '').strip()
    numero_form = (request.form.get('numero') or '').strip()

    errors, payload = incluir_service.validar_entrada(cliente, cpf, valor, data)

    if errors:
        for e in errors:
            flash(e, 'error')
        return redirect(url_for('index'))

    ok, last_err = incluir_service.salvar(payload, numero_form)

    if not ok:
        flash('Erro ao salvar o contrato: ' + str(last_err), 'error')
        return redirect(url_for('index'))

    flash('Contrato incluído com sucesso.', 'success')
    return redirect(url_for('consultar_contratos'))


@app.route('/consultar')
def consultar_contratos():
    # Página separada para consulta da base `contratos_bancarios`
    q = request.args.get('q', '')
    # Sempre usar "auto" - detecção automática por nome, CPF ou número
    contratos = consultar_service.consultar(q, by='auto')
    return render_template('consultar.html', contratos=contratos)


@app.route('/excluir/<int:contrato_id>', methods=['POST'])
def excluir_contrato(contrato_id: int):
    try:
        excluir_service.excluir(contrato_id)
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

    updates, err_msg = editar_service.preparar_updates(numero, cliente, cpf, valor, data)
    if err_msg:
        flash(err_msg, 'error')
        return redirect(url_for('index'))
    if updates is None:
        flash('Dados de edição inválidos', 'error')
        return redirect(url_for('index'))

    ok, err = editar_service.editar(contrato_id, updates)
    if not ok:
        if isinstance(err, ValueError):
            flash(str(err), 'error')
        else:
            traceback.print_exc()
            flash('Erro ao editar contrato: ' + str(err), 'error')
        return redirect(url_for('index'))

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=False)