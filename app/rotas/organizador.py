"""
Área do organizador (/organizador/...): painel, eventos, ingressos, loja,
pulseiras, transações, equipe e conta. Toda rota usa @exige_organizador.
"""
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import seguranca
from app.dao import cartao_dao, evento_dao, funcionario_dao, ingresso_dao, produto_dao, relatorio_dao
from app.modelos import RegraNegocio
from app.seguranca import exige_organizador, exigir_evento, organizador_atual
from app.servicos import (conta_servico, equipe_servico, evento_servico, ingresso_servico, produto_servico,
                          qrcode_servico, venda_servico)
from app.utilidades import normalizar_uid

bp = Blueprint("organizador", __name__, url_prefix="/organizador")


def _marcado(nome):
    """Checkbox marcado no formulário?"""
    return request.form.get(nome) == "true"


def _id_ou_none(texto):
    return int(texto) if texto and texto.isdigit() else None


def _maior(itens):
    return max((i["valor"] for i in itens), default=0)


# ------------------------------------------------------------ painel (RF09 / RNF05)
@bp.get("")
@bp.get("/")
@exige_organizador
def painel():
    evento = exigir_evento()
    id = evento["id"]
    vendidos = relatorio_dao.ingressos_vendidos(id)
    faturamento_ingressos = relatorio_dao.faturamento_ingressos(id)
    vendas = relatorio_dao.vendas_liquidas(id)
    por_ponto = relatorio_dao.vendas_por_ponto(id)
    por_lote = relatorio_dao.ingressos_por_lote(id)
    mais_vendidos = relatorio_dao.produtos_mais_vendidos(id, 5)
    return render_template(
        "organizador/painel.html", pagina="painel",
        vendidos=vendidos,
        entradas=relatorio_dao.entradas(id),
        faturamento=faturamento_ingressos + vendas,
        faturamento_ingressos=faturamento_ingressos,
        vendas=vendas,
        recargas=relatorio_dao.recargas(id),
        saldo_pulseiras=relatorio_dao.saldo_nas_pulseiras(id),
        pulseiras=relatorio_dao.pulseiras_ativas(id),
        vendas_por_ponto=por_ponto, ingressos_por_lote=por_lote, mais_vendidos=mais_vendidos,
        # Maior valor de cada gráfico: a maior barra ocupa 100% da largura
        max_ponto=_maior(por_ponto), max_lote=_maior(por_lote), max_produto=_maior(mais_vendidos),
        ultimas=cartao_dao.transacoes(id, None, 8),
        # "Primeiros passos": aparece enquanto o evento ainda não está pronto
        tem_produtos=len(produto_dao.produtos(id, False)) > 0,
        tem_equipe=len(funcionario_dao.listar(id)) > 0,
    )


@bp.post("/evento-atual")
@exige_organizador
def trocar_evento():
    """Troca o evento aberto (seletor do menu lateral) e volta para a mesma tela."""
    seguranca.abrir_evento(_id_ou_none(request.form.get("evento_id")))
    caminho = urlparse(request.referrer or "").path
    if caminho.startswith("/organizador/") and "/ingressos/" not in caminho:
        return redirect(caminho)
    return redirect(url_for("organizador.painel"))


# ------------------------------------------------------------ eventos (RF02)
@bp.get("/eventos")
@exige_organizador
def eventos():
    return render_template("organizador/eventos.html", pagina="eventos",
                           classificacoes=evento_servico.CLASSIFICACOES)


@bp.post("/eventos")
@exige_organizador
def criar_evento():
    f = request.form
    id = evento_servico.criar(organizador_atual(), f.get("nome"), f.get("data_hora"), f.get("local_evento"),
                              f.get("classificacao"), f.get("capacidade"))
    seguranca.abrir_evento(id)
    evento = evento_dao.buscar_por_id(id)
    flash(f"Evento criado! O código de acesso da equipe é {evento['codigo_acesso']}.", "ok")
    return redirect(url_for("organizador.painel"))


@bp.post("/eventos/<int:id>")
@exige_organizador
def editar_evento(id):
    f = request.form
    evento_servico.editar(organizador_atual(), id, f.get("nome"), f.get("data_hora"), f.get("local_evento"),
                          f.get("classificacao"), f.get("capacidade"))
    flash("Evento atualizado.", "ok")
    return redirect(url_for("organizador.eventos"))


@bp.post("/eventos/<int:id>/abrir")
@exige_organizador
def abrir_evento(id):
    seguranca.abrir_evento(id)
    return redirect(url_for("organizador.painel"))


# ------------------------------------------------------------ ingressos (RF04)
@bp.get("/ingressos")
@exige_organizador
def ingressos():
    evento = exigir_evento()
    busca = request.args.get("busca", "")
    return render_template(
        "organizador/ingressos.html", pagina="ingressos",
        lotes=ingresso_dao.lotes(evento["id"]),
        ingressos=ingresso_dao.listar(evento["id"], busca),
        busca=busca,
        usados=ingresso_dao.contar(evento["id"], "usado"),
        validos=ingresso_dao.contar(evento["id"], "valido"),
        lugares_em_lotes=ingresso_dao.total_de_lugares_em_lotes(evento["id"]),
    )


@bp.post("/ingressos/lotes")
@exige_organizador
def criar_lote():
    f = request.form
    ingresso_servico.criar_lote(exigir_evento(), f.get("nome"), f.get("preco"), f.get("quantidade"))
    flash(f"Lote {f.get('nome', '').strip()} criado.", "ok")
    return redirect(url_for("organizador.ingressos"))


@bp.post("/ingressos")
@exige_organizador
def emitir_ingresso():
    f = request.form
    lote_id = _id_ou_none(f.get("lote_id"))
    if lote_id is None:
        raise RegraNegocio("Escolha o lote.")
    ingresso = ingresso_servico.emitir(exigir_evento()["id"], lote_id, f.get("nome"), f.get("email"))
    flash(f"Ingresso emitido para {ingresso['nome_participante']}.", "ok")
    return redirect(url_for("organizador.ingresso", id=ingresso["id"]))


@bp.get("/ingressos/<int:id>")
@exige_organizador
def ingresso(id):
    ingresso = ingresso_dao.buscar(id, exigir_evento()["id"])
    if ingresso is None:
        raise RegraNegocio("Ingresso não encontrado.")
    return render_template("organizador/ingresso.html", pagina="ingressos", ingresso=ingresso)


@bp.get("/ingressos/<int:id>/qr.svg")
@exige_organizador
def qr_code(id):
    """Imagem do QR Code (usada na página do ingresso e na impressão)."""
    ingresso = ingresso_dao.buscar(id, exigir_evento()["id"])
    if ingresso is None:
        raise RegraNegocio("Ingresso não encontrado.")
    return qrcode_servico.svg(ingresso["qr_code"]), 200, {"Content-Type": "image/svg+xml"}


@bp.post("/ingressos/<int:id>/cancelar")
@exige_organizador
def cancelar_ingresso(id):
    ingresso_servico.cancelar(exigir_evento()["id"], id)
    flash("Ingresso cancelado.", "ok")
    return redirect(url_for("organizador.ingresso", id=id))


# ------------------------------------------------------------ loja (RF05)
@bp.get("/produtos")
@exige_organizador
def produtos():
    evento_id = exigir_evento()["id"]
    return render_template("organizador/produtos.html", pagina="produtos",
                           pontos=produto_dao.pontos(evento_id), produtos=produto_dao.produtos(evento_id, False))


@bp.post("/produtos/pontos")
@exige_organizador
def criar_ponto():
    produto_servico.criar_ponto(exigir_evento()["id"], request.form.get("nome"))
    flash("Ponto de venda criado.", "ok")
    return redirect(url_for("organizador.produtos"))


@bp.post("/produtos")
@exige_organizador
def criar_produto():
    f = request.form
    produto_servico.criar_produto(exigir_evento()["id"], f.get("nome"), f.get("categoria"), f.get("preco"),
                                  f.get("estoque"))
    flash(f"Produto {f.get('nome', '').strip()} cadastrado.", "ok")
    return redirect(url_for("organizador.produtos"))


@bp.post("/produtos/<int:id>")
@exige_organizador
def atualizar_produto(id):
    produto_servico.atualizar_produto(exigir_evento()["id"], id, request.form.get("preco"),
                                      request.form.get("estoque"))
    flash("Produto atualizado.", "ok")
    return redirect(url_for("organizador.produtos"))


@bp.post("/produtos/<int:id>/ativo")
@exige_organizador
def alternar_produto(id):
    produto_dao.alternar_ativo(id, exigir_evento()["id"])
    return redirect(url_for("organizador.produtos"))


# ------------------------------------------------------------ pulseiras e transações (RF06)
@bp.get("/pulseiras")
@exige_organizador
def pulseiras():
    evento_id = exigir_evento()["id"]
    busca = request.args.get("busca", "")
    return render_template("organizador/pulseiras.html", pagina="pulseiras",
                           cartoes=cartao_dao.listar(evento_id, busca), busca=busca,
                           saldo_total=relatorio_dao.saldo_nas_pulseiras(evento_id),
                           ativas=relatorio_dao.pulseiras_ativas(evento_id))


@bp.post("/pulseiras")
@exige_organizador
def cadastrar_pulseira():
    evento_id = exigir_evento()["id"]
    uid = normalizar_uid(request.form.get("uid"))
    if len(uid) < 8:
        raise RegraNegocio("Código da pulseira inválido.")
    if cartao_dao.buscar_por_uid(evento_id, uid):
        raise RegraNegocio("Essa pulseira já está cadastrada.")
    cartao_dao.inserir(evento_id, uid)
    flash(f"Pulseira {uid} cadastrada.", "ok")
    return redirect(url_for("organizador.pulseiras"))


@bp.post("/pulseiras/<int:id>/ativo")
@exige_organizador
def bloquear_pulseira(id):
    cartao_dao.alternar_ativo(id, exigir_evento()["id"])
    return redirect(url_for("organizador.pulseiras"))


@bp.get("/transacoes")
@exige_organizador
def transacoes():
    tipo = request.args.get("tipo", "")
    return render_template("organizador/transacoes.html", pagina="transacoes", tipo=tipo,
                           transacoes=cartao_dao.transacoes(exigir_evento()["id"], tipo, 150))


@bp.post("/transacoes/<int:id>/estornar")
@exige_organizador
def estornar(id):
    venda_servico.estornar(exigir_evento()["id"], id)
    flash("Compra estornada. O valor voltou para a pulseira.", "ok")
    return redirect(url_for("organizador.transacoes"))


# ------------------------------------------------------------ equipe (RF08)
@bp.get("/equipe")
@exige_organizador
def equipe():
    evento_id = exigir_evento()["id"]
    return render_template("organizador/equipe.html", pagina="equipe",
                           membros=funcionario_dao.listar(evento_id), pontos=produto_dao.pontos(evento_id))


@bp.post("/equipe")
@exige_organizador
def criar_acesso():
    f = request.form
    evento = exigir_evento()
    equipe_servico.criar(organizador_atual(), evento["id"], f.get("nome"), f.get("usuario_equipe"), f.get("senha"),
                         _id_ou_none(f.get("ponto_id")), _marcado("perm_escanear"), _marcado("perm_pdv"),
                         _marcado("perm_caixa"), _marcado("perm_relatorios"))
    flash(f"Acesso criado. Passe para {f.get('nome', '').strip()}: código {evento['codigo_acesso']}, "
          f"usuário {f.get('usuario_equipe', '').strip().lower()} e a senha.", "ok")
    return redirect(url_for("organizador.equipe"))


@bp.post("/equipe/<int:id>/permissoes")
@exige_organizador
def permissoes(id):
    equipe_servico.atualizar_permissoes(exigir_evento()["id"], id, _id_ou_none(request.form.get("ponto_id")),
                                        _marcado("perm_escanear"), _marcado("perm_pdv"),
                                        _marcado("perm_caixa"), _marcado("perm_relatorios"))
    flash("Permissões salvas.", "ok")
    return redirect(url_for("organizador.equipe"))


@bp.post("/equipe/<int:id>/ativo")
@exige_organizador
def alternar_membro(id):
    funcionario_dao.alternar_ativo(id, exigir_evento()["id"])
    return redirect(url_for("organizador.equipe"))


@bp.post("/equipe/<int:id>/senha")
@exige_organizador
def redefinir_senha(id):
    equipe_servico.redefinir_senha(exigir_evento()["id"], id, request.form.get("senha"))
    flash("Senha redefinida.", "ok")
    return redirect(url_for("organizador.equipe"))


# ------------------------------------------------------------ conta e aparência
@bp.get("/conta")
@exige_organizador
def conta():
    return render_template("organizador/conta.html", pagina="conta")


@bp.post("/conta/aparencia")
@exige_organizador
def aparencia():
    conta_servico.alterar_aparencia(organizador_atual()["id"], request.form.get("tema"), request.form.get("modo"))
    flash("Aparência salva.", "ok")
    return redirect(url_for("organizador.conta"))


@bp.post("/conta/aparencia/rapida")
@exige_organizador
def aparencia_rapida():
    """Chamado pelo JavaScript do botão claro/escuro (salva sem recarregar a página)."""
    conta_servico.alterar_aparencia(organizador_atual()["id"], request.form.get("tema"), request.form.get("modo"))
    return "", 204


@bp.post("/conta/dados")
@exige_organizador
def dados():
    conta_servico.alterar_nome(organizador_atual()["id"], request.form.get("nome"))
    flash("Dados atualizados.", "ok")
    return redirect(url_for("organizador.conta"))


@bp.post("/conta/senha")
@exige_organizador
def senha():
    f = request.form
    conta_servico.alterar_senha(organizador_atual()["id"], f.get("atual"), f.get("nova"), f.get("confirmacao"))
    flash("Senha alterada.", "ok")
    return redirect(url_for("organizador.conta"))
