"""
Tudo que mexe com saldo da pulseira (RF05 e RF06): venda, recarga e estorno.
Cada operação roda dentro de banco.transacao(): se qualquer passo falhar
(ex.: acabou o estoque no meio da compra), o banco desfaz tudo (rollback).
"""
import psycopg

from app import banco
from app.dao import cartao_dao, produto_dao
from app.formatador import reais
from app.modelos import RegraNegocio
from app.utilidades import normalizar_uid, para_centavos

RECARGA_MAXIMA = 100_000   # R$ 1.000,00
FORMAS_DE_PAGAMENTO = ["pix", "cartao", "dinheiro"]


def montar_carrinho(evento_id, quantidades):
    """
    Monta o carrinho com os preços do BANCO (nunca confia no preço vindo da tela).
    quantidades = {id_do_produto: quantidade}
    """
    itens = []
    for produto_id, qtd in quantidades.items():
        if qtd <= 0:
            continue
        if qtd > 99:
            raise RegraNegocio("Quantidade muito alta para um único item.")
        p = produto_dao.buscar(produto_id, evento_id)
        if p is None or not p["ativo"]:
            raise RegraNegocio("Produto indisponível.")
        itens.append({"produto_id": p["id"], "nome": p["nome"], "preco_unitario": p["preco"],
                      "quantidade": qtd, "subtotal": p["preco"] * qtd})
    if not itens:
        raise RegraNegocio("O carrinho está vazio.")
    return itens


def total(itens):
    return sum(item["subtotal"] for item in itens)


def vender(func, ponto_id, quantidades, uid_texto):
    """Debita a pulseira, baixa o estoque e registra a venda. Devolve o id da transação."""
    evento_id = func["evento_id"]
    ponto = produto_dao.buscar_ponto(ponto_id, evento_id)
    if ponto is None:
        raise RegraNegocio("Ponto de venda inválido.")
    itens = montar_carrinho(evento_id, quantidades)
    valor = total(itens)
    cartao = _pulseira_ativa(evento_id, uid_texto)

    with banco.transacao():
        if not cartao_dao.debitar(cartao["id"], valor):
            raise RegraNegocio(f"Saldo insuficiente. A pulseira tem {reais(cartao['saldo'])} "
                               f"e a compra é de {reais(valor)}.")
        for item in itens:
            if not produto_dao.baixar_estoque(item["produto_id"], item["quantidade"]):
                raise RegraNegocio(f"Estoque insuficiente de {item['nome']}.")
        transacao_id = cartao_dao.inserir_transacao(cartao["id"], func["id"], ponto["id"], valor,
                                                    "debito", None, None)
        for item in itens:
            cartao_dao.inserir_item(transacao_id, item)
    return transacao_id


def recarregar(func, uid_texto, valor_texto, forma):
    """Recarga no caixa. Se a pulseira ainda não existe no evento, ela é ativada aqui."""
    evento_id = func["evento_id"]
    uid = _uid(uid_texto)
    valor = para_centavos(valor_texto)
    if valor <= 0 or valor > RECARGA_MAXIMA:
        raise RegraNegocio(f"A recarga precisa ser entre R$ 0,01 e {reais(RECARGA_MAXIMA)}.")
    if forma not in FORMAS_DE_PAGAMENTO:
        raise RegraNegocio("Escolha a forma de pagamento.")

    with banco.transacao():
        cartao = cartao_dao.buscar_por_uid(evento_id, uid)
        if cartao is None:
            cartao = cartao_dao.buscar(cartao_dao.inserir(evento_id, uid), evento_id)
        if not cartao["ativo"]:
            raise RegraNegocio("Pulseira bloqueada. Procure o organizador.")
        cartao_dao.creditar(cartao["id"], valor)
        cartao_dao.inserir_transacao(cartao["id"], func["id"], None, valor, "recarga", forma, None)
    return cartao_dao.buscar(cartao["id"], evento_id)


def consultar(evento_id, uid_texto):
    cartao = cartao_dao.buscar_por_uid(evento_id, _uid(uid_texto))
    if cartao is None:
        raise RegraNegocio("Pulseira não cadastrada neste evento.")
    return cartao


def estornar(evento_id, transacao_id):
    """Devolve o valor de uma compra para a pulseira e o estoque dos produtos."""
    t = cartao_dao.buscar_transacao(transacao_id, evento_id)
    if t is None:
        raise RegraNegocio("Transação não encontrada.")
    if t["tipo"] != "debito":
        raise RegraNegocio("Só compras podem ser estornadas.")
    if cartao_dao.ja_estornada(t["id"]):
        raise RegraNegocio("Essa compra já foi estornada.")
    try:
        with banco.transacao():
            cartao_dao.creditar(t["cartao_id"], t["valor"])
            for item in cartao_dao.itens(t["id"]):
                produto_dao.devolver_estoque(item["produto_id"], item["quantidade"])
            cartao_dao.inserir_transacao(t["cartao_id"], None, t["ponto_id"], t["valor"], "estorno", None, t["id"])
    except psycopg.errors.UniqueViolation:
        # Dois cliques ao mesmo tempo: o índice único do banco barrou o segundo estorno
        raise RegraNegocio("Essa compra já foi estornada.") from None


# ------------------------------------------------------------ auxiliares
def _pulseira_ativa(evento_id, uid_texto):
    cartao = cartao_dao.buscar_por_uid(evento_id, _uid(uid_texto))
    if cartao is None:
        raise RegraNegocio("Pulseira não cadastrada. Faça uma recarga no caixa.")
    if not cartao["ativo"]:
        raise RegraNegocio("Pulseira bloqueada. Procure o organizador.")
    return cartao


def _uid(texto):
    uid = normalizar_uid(texto)
    if len(uid) < 8:
        raise RegraNegocio("Aproxime a pulseira ou digite o código dela.")
    return uid
