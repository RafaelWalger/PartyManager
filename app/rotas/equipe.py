"""
"Modo operador" da equipe (/equipe/...). É uma área separada da do organizador:
tela cheia, botões grandes, e só aparece o que o funcionário tem permissão.
Toda rota usa @exige_funcionario, que deixa g.func e g.evento prontos.
"""
from flask import Blueprint, flash, g, get_flashed_messages, redirect, render_template, request, url_for

from app.dao import cartao_dao, ingresso_dao, produto_dao, relatorio_dao
from app.formatador import hora, reais
from app.modelos import RegraNegocio
from app.seguranca import exige_funcionario, exigir_permissao
from app.servicos import ingresso_servico, venda_servico

bp = Blueprint("equipe", __name__, url_prefix="/equipe")


@bp.get("")
@bp.get("/")
@exige_funcionario
def inicio():
    return render_template("equipe/inicio.html")


# ------------------------------------------------------------ portaria (RF07)
@bp.get("/portaria")
@exige_funcionario
def portaria():
    exigir_permissao(g.func["perm_escanear"])
    # Resultado da última leitura (guardado pelo POST logo abaixo)
    leituras = get_flashed_messages(category_filter=["portaria"])
    return render_template("equipe/portaria.html", leitura=leituras[0] if leituras else None,
                           entradas=relatorio_dao.entradas(g.evento["id"]))


@bp.post("/portaria")
@exige_funcionario
def validar():
    exigir_permissao(g.func["perm_escanear"])
    codigo = request.form.get("codigo", "")
    situacao, ingresso = ingresso_servico.validar(g.func["evento_id"], codigo)
    leitura = {"situacao": situacao, "codigo": codigo.strip().upper()}
    if ingresso:
        leitura["participante"] = ingresso["nome_participante"]
        leitura["lote"] = ingresso["lote_nome"]
        leitura["hora_entrada"] = hora(ingresso["usado_em"]) if ingresso["usado_em"] else None
    flash(leitura, "portaria")
    return redirect(url_for("equipe.portaria"))


@bp.get("/acesso")
@exige_funcionario
def lista_de_acesso():
    exigir_permissao(g.func["perm_escanear"])
    busca = request.args.get("busca", "")
    evento_id = g.evento["id"]
    return render_template("equipe/acesso.html", ingressos=ingresso_dao.listar(evento_id, busca), busca=busca,
                           entradas=relatorio_dao.entradas(evento_id),
                           vendidos=relatorio_dao.ingressos_vendidos(evento_id))


# ------------------------------------------------------------ ponto de venda (RF05)
@bp.get("/pdv")
@exige_funcionario
def pdv():
    exigir_permissao(g.func["perm_pdv"])
    pontos = produto_dao.pontos(g.func["evento_id"])
    if not pontos:
        raise RegraNegocio("O organizador ainda não cadastrou pontos de venda.")
    # Funcionário com ponto fixo fica sempre nele; os outros escolhem
    pedido = request.args.get("ponto_id", type=int)
    alvo = g.func["ponto_id"] or pedido
    ponto = next((p for p in pontos if p["id"] == alvo), pontos[0])
    return render_template("equipe/pdv.html", pontos=pontos, ponto=ponto,
                           produtos=produto_dao.produtos(g.func["evento_id"], True))


@bp.post("/pdv/cobrar")
@exige_funcionario
def cobrar():
    """Mostra a tela de cobrança com o carrinho (ainda não debita nada)."""
    exigir_permissao(g.func["perm_pdv"])
    return _tela_cobranca(request.form.get("ponto_id", type=int), _ler_carrinho(), None)


@bp.post("/pdv/confirmar")
@exige_funcionario
def confirmar():
    """A pulseira foi lida: debita o saldo, baixa o estoque e registra a venda."""
    exigir_permissao(g.func["perm_pdv"])
    ponto_id = request.form.get("ponto_id", type=int)
    quantidades = _ler_carrinho()
    try:
        transacao_id = venda_servico.vender(g.func, ponto_id, quantidades, request.form.get("uid", ""))
    except RegraNegocio as e:
        return _tela_cobranca(ponto_id, quantidades, str(e))
    return redirect(url_for("equipe.recibo", id=transacao_id))


@bp.get("/vendas/<int:id>")
@exige_funcionario
def recibo(id):
    exigir_permissao(g.func["perm_pdv"] or g.func["perm_caixa"])
    transacao = cartao_dao.buscar_transacao(id, g.func["evento_id"])
    if transacao is None:
        raise RegraNegocio("Venda não encontrada.")
    return render_template("equipe/recibo.html", transacao=transacao, itens=cartao_dao.itens(id),
                           cartao=cartao_dao.buscar(transacao["cartao_id"], g.func["evento_id"]))


def _tela_cobranca(ponto_id, quantidades, erro):
    ponto = produto_dao.buscar_ponto(ponto_id, g.func["evento_id"]) if ponto_id else None
    if ponto is None:
        raise RegraNegocio("Ponto de venda inválido.")
    itens = venda_servico.montar_carrinho(g.func["evento_id"], quantidades)
    return render_template("equipe/cobrar.html", ponto=ponto, itens=itens, total=venda_servico.total(itens),
                           erro=erro)


def _ler_carrinho():
    """Os campos do carrinho chegam como q_12=2 (produto 12, quantidade 2)."""
    quantidades = {}
    for nome, valor in request.form.items():
        if nome.startswith("q_"):
            try:
                produto_id, qtd = int(nome[2:]), int(valor.strip())
            except ValueError:
                raise RegraNegocio("Carrinho inválido.") from None
            quantidades[produto_id] = quantidades.get(produto_id, 0) + qtd
    return quantidades


# ------------------------------------------------------------ caixa de pulseiras (RF06)
@bp.get("/caixa")
@exige_funcionario
def caixa():
    exigir_permissao(g.func["perm_caixa"])
    uid = request.args.get("uid", "")
    cartao, historico, erro = None, [], None
    if uid.strip():
        try:
            cartao = venda_servico.consultar(g.func["evento_id"], uid)
            historico = cartao_dao.transacoes_do_cartao(cartao["id"], 6)
        except RegraNegocio as e:
            erro = str(e)
    return render_template("equipe/caixa.html", uid=uid, cartao=cartao, historico=historico, erro=erro)


@bp.post("/caixa/recarga")
@exige_funcionario
def recarga():
    exigir_permissao(g.func["perm_caixa"])
    f = request.form
    cartao = venda_servico.recarregar(g.func, f.get("uid"), f.get("valor"), f.get("forma", ""))
    flash(f"Recarga feita! Novo saldo da pulseira: {reais(cartao['saldo'])}.", "ok")
    return redirect(url_for("equipe.caixa", uid=cartao["uid_nfc"]))


# ------------------------------------------------------------ resumo do evento
@bp.get("/resumo")
@exige_funcionario
def resumo():
    exigir_permissao(g.func["perm_relatorios"])
    f = g.func
    return render_template(
        "equipe/resumo.html",
        entradas=relatorio_dao.entradas(g.evento["id"]),
        vendidos=relatorio_dao.ingressos_vendidos(g.evento["id"]),
        minhas_vendas=relatorio_dao.vendas_do_funcionario(f["id"]),
        vendas_do_ponto=relatorio_dao.vendas_do_ponto(f["ponto_id"]) if f["ponto_id"] else None,
        minhas_transacoes=cartao_dao.transacoes_do_funcionario(f["id"], 10),
    )
