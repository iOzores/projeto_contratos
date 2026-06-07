from dotenv import load_dotenv
import os
from pathlib import Path

# Carregar .env do diretório do projeto
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

from flask import Flask, render_template, request, redirect, url_for, flash, Response
from db import ContratoDB
from Classes import (
    IncluirContratoService,
    ConsultarContratoService,
    EditarContratoService,
    ExcluirContratoService,
)
from Classes.simulador import SimuladorService
from Classes.utils import parse_money_br
from Classes.formatters import register_jinja_filters
import traceback
import csv
import io

app = Flask(__name__)
app.secret_key = "dev-secret-for-flash-messages"
register_jinja_filters(app)

# Instância compartilhada do banco (cria tabela se necessário)
db = ContratoDB()
incluir_service = IncluirContratoService(db)
consultar_service = ConsultarContratoService(db)
editar_service = EditarContratoService(db)
excluir_service = ExcluirContratoService(db)
simulador_service = SimuladorService()


def _resumo_parcelas(parcelas):
    total_pago = round(sum(parcela["prestacao"] for parcela in parcelas), 2) if parcelas else 0.0
    total_juros = round(sum(parcela["juros"] for parcela in parcelas), 2) if parcelas else 0.0
    return {
        "total_pago": total_pago,
        "total_juros": total_juros,
    }

@app.route('/')
def index():
    # Não retornar os registros de `contratos_bancarios` para não listar na home
    return render_template('index.html', contratos=None)


@app.route('/incluir', methods=['GET', 'POST'])
def incluir_contrato():
    # GET: mostra o formulário de inclusão
    if request.method == 'GET':
        numero_preview = incluir_service.gerar_numero_preview()
        valor_form = (request.args.get('valor') or '').strip()
        taxa_juros_form = (request.args.get('taxa_juros') or '').strip()
        prazo_meses_form = (request.args.get('prazo_meses') or '12').strip()
        sistema_amortizacao_form = (request.args.get('sistema') or '').strip().upper()
        return render_template(
            'incluir.html',
            numero_preview=numero_preview,
            valor_form=valor_form,
            taxa_juros_form=taxa_juros_form,
            prazo_meses_form=prazo_meses_form,
            sistema_amortizacao_form=sistema_amortizacao_form,
        )

    cliente = (request.form.get('cliente') or '').strip()
    cpf = (request.form.get('cpf') or '').strip()
    valor = (request.form.get('valor') or '').strip()
    taxa_juros = (request.form.get('taxa_juros') or '').strip()
    data_nascimento = (request.form.get('data_nascimento') or '').strip()
    prazo_meses = (request.form.get('prazo_meses') or '').strip()
    sistema_amortizacao = (request.form.get('sistema_amortizacao') or '').strip().upper()
    data = (request.form.get('data') or '').strip()
    numero_form = (request.form.get('numero') or '').strip()

    errors, payload = incluir_service.validar_entrada(cliente, cpf, valor, data, taxa_juros=taxa_juros, data_nascimento=data_nascimento, prazo_meses=prazo_meses, sistema_amortizacao=sistema_amortizacao)

    if errors:
        for e in errors:
            flash(e, 'error')
        return redirect(url_for('index'))

    ok, last_err, contrato_id = incluir_service.salvar(payload, numero_form)

    if not ok:
        flash('Erro ao salvar o contrato: ' + str(last_err), 'error')
        return redirect(url_for('index'))

    if contrato_id and payload.get("sistema_amortizacao") in {"SAC", "PRICE"}:
        if payload["sistema_amortizacao"] == "SAC":
            parcelas = simulador_service.simular_sac(payload["valor"], payload["taxa_juros"], payload["prazo_meses"])
        else:
            parcelas = simulador_service.simular_price(payload["valor"], payload["taxa_juros"], payload["prazo_meses"])
        db.replace_parcelas(contrato_id, payload["sistema_amortizacao"], parcelas)

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
    prazo_meses = (request.form.get('prazo_meses') or '').strip()
    data = (request.form.get('data') or '').strip()

    if not cliente or not cpf or not valor or not data:
        flash('Preencha todos os campos obrigatórios.', 'error')
        return render_template('editar.html', contrato=contrato)

    updates, err_msg = editar_service.preparar_updates(None, cliente, cpf, valor, data, taxa_juros=taxa_juros, data_nascimento=data_nascimento, prazo_meses=prazo_meses)
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

    if getattr(contrato, "sistema_amortizacao", None) in {"SAC", "PRICE"}:
        valor_calc = updates.get("valor", contrato.valor)
        taxa_calc = updates.get("taxa_juros", contrato.taxa_juros)
        prazo_calc = updates.get("prazo_meses", contrato.prazo_meses)
        if contrato.sistema_amortizacao == "SAC":
            parcelas = simulador_service.simular_sac(valor_calc, taxa_calc, prazo_calc)
        else:
            parcelas = simulador_service.simular_price(valor_calc, taxa_calc, prazo_calc)
        db.replace_parcelas(contrato_id, contrato.sistema_amortizacao, parcelas)

    flash('Contrato atualizado com sucesso.', 'success')
    return redirect(url_for('consultar_contratos'))


@app.route('/simular', methods=['GET', 'POST'])
def simular_emprestimo():
    valor_form = (request.values.get('valor') or '').strip()
    taxa_juros_form = (request.values.get('taxa_juros') or '').strip()
    meses_form = (request.values.get('meses') or '12').strip()

    simulacao_realizada = False
    sac_parcelas = []
    price_parcelas = []
    sac_resumo = _resumo_parcelas([])
    price_resumo = _resumo_parcelas([])

    if request.method == 'POST':
        errors = []

        try:
            valor_total = parse_money_br(valor_form)
        except Exception:
            errors.append('Valor do empréstimo inválido.')
            valor_total = None

        try:
            taxa_juros = parse_money_br(taxa_juros_form)
        except Exception:
            errors.append('Taxa de juros inválida.')
            taxa_juros = None

        try:
            meses = int(meses_form)
            if meses <= 0:
                raise ValueError()
        except Exception:
            errors.append('Prazo contratado inválido.')
            meses = None

        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            sac_parcelas = simulador_service.simular_sac(valor_total, taxa_juros, meses)
            price_parcelas = simulador_service.simular_price(valor_total, taxa_juros, meses)
            sac_resumo = _resumo_parcelas(sac_parcelas)
            price_resumo = _resumo_parcelas(price_parcelas)
            simulacao_realizada = True

    return render_template(
        'simular.html',
        valor_form=valor_form,
        taxa_juros_form=taxa_juros_form,
        meses_form=meses_form,
        simulacao_realizada=simulacao_realizada,
        sac_parcelas=sac_parcelas,
        price_parcelas=price_parcelas,
        sac_resumo=sac_resumo,
        price_resumo=price_resumo,
    )


@app.route('/simular/<int:contrato_id>', methods=['GET'])
def simular_contrato(contrato_id: int):
    contrato = db.get_by_id(contrato_id)
    if contrato is None:
        flash('Contrato não encontrado para simulação.', 'error')
        return redirect(url_for('simular_emprestimo'))

    return redirect(url_for('simular_emprestimo', valor=contrato.valor, taxa_juros=contrato.taxa_juros, meses=getattr(contrato, 'prazo_meses', 12) or 12))


@app.route('/exportar')
def exportar_contratos():
    # Pega o mesmo filtro da consulta
    q = request.args.get('q', '')
    contratos = consultar_service.consultar(q, by='auto')
    
    # Usa um arquivo virtual na memória para montar o CSV
    si = io.StringIO()
    
    # Dica de ouro: Inserir o BOM (Byte Order Mark) para o Excel Brasileiro abrir a acentuação perfeitamente
    si.write('\ufeff') 
    
    # O delimiter padrão no Brasil costuma ser ponto-e-vírgula ';'
    cw = csv.writer(si, delimiter=';') 
    
    # Escrevendo a linha de cabeçalho
    cw.writerow(['ID', 'Número', 'Cliente', 'CPF', 'Valor (R$)', 'Prazo (meses)', 'Sistema', 'Taxa Juros (%)', 'Data de Nascimento', 'Data Contrato'])
    
    # Escrevendo as linhas dos contratos
    for c in contratos:
        cw.writerow([c.id, c.numero, c.cliente, c.cliente_cpf, c.valor, getattr(c, 'prazo_meses', ''), getattr(c, 'sistema_amortizacao', '') or '', c.taxa_juros, c.data_nascimento, c.data])
        
    output = si.getvalue()
    
    return Response(
        output,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=relatorio_ozzbank.csv"}
    )

if __name__ == '__main__':
    app.run(debug=False)
