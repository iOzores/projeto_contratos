from dotenv import load_dotenv
load_dotenv(override=True)

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
    taxa_juros = (request.form.get('taxa_juros') or '').strip()
    data_nascimento = (request.form.get('data_nascimento') or '').strip()
    data = (request.form.get('data') or '').strip()
    numero_form = (request.form.get('numero') or '').strip()

    errors, payload = incluir_service.validar_entrada(cliente, cpf, valor, data, taxa_juros=taxa_juros, data_nascimento=data_nascimento)

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
    contratos = consultar_service.consultar(q, by='auto')
    return render_template('consultar.html', contratos=contratos)


@app.route('/excluir/<int:contrato_id>', methods=['POST'])
def excluir_contrato(contrato_id: int):
    q = (request.form.get('q') or '').strip()
    try:
        deleted = excluir_service.excluir(contrato_id)
        if deleted:
            flash('Contrato excluído com sucesso.', 'success')
        else:
            flash('Contrato não encontrado para exclusão.', 'error')
    except Exception as e:
        traceback.print_exc()
        flash('Erro ao excluir contrato: ' + str(e), 'error')
    return redirect(url_for('consultar_contratos', q=q))


@app.route('/editar/<int:contrato_id>', methods=['GET', 'POST'])
def editar_contrato(contrato_id: int):
    contrato = db.get_by_id(contrato_id)
    if contrato is None:
        flash('Contrato não encontrado.', 'error')
        return redirect(url_for('consultar_contratos'))

    if request.method == 'GET':
        return render_template('editar.html', contrato=contrato)

    cliente = (request.form.get('cliente') or '').strip()
    cpf = (request.form.get('cpf') or '').strip()
    valor = (request.form.get('valor') or '').strip()
    taxa_juros = (request.form.get('taxa_juros') or '').strip()
    data_nascimento = (request.form.get('data_nascimento') or '').strip()
    data = (request.form.get('data') or '').strip()

    if not cliente or not cpf or not valor or not data:
        flash('Preencha todos os campos obrigatórios.', 'error')
        return render_template('editar.html', contrato=contrato)

    updates, err_msg = editar_service.preparar_updates(None, cliente, cpf, valor, data, taxa_juros=taxa_juros, data_nascimento=data_nascimento)
    if err_msg:
        flash(err_msg, 'error')
        return render_template('editar.html', contrato=contrato)
    if updates is None:
        flash('Dados de edição inválidos', 'error')
        return render_template('editar.html', contrato=contrato)

    ok, err = editar_service.editar(contrato_id, updates)
    if not ok:
        if isinstance(err, ValueError):
            flash(str(err), 'error')
        else:
            traceback.print_exc()
            flash('Erro ao editar contrato: ' + str(err), 'error')
        return render_template('editar.html', contrato=contrato)

    flash('Contrato atualizado com sucesso.', 'success')
    return redirect(url_for('consultar_contratos'))


if __name__ == '__main__':
    app.run(debug=False)