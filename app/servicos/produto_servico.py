"""Pontos de venda e produtos da loja do evento (RF05)."""
from app.dao import produto_dao
from app.modelos import RegraNegocio
from app.utilidades import obrigatorio, para_centavos, para_inteiro

CATEGORIAS = ["bebida", "comida", "loja"]


def criar_ponto(evento_id, nome):
    nome = obrigatorio(nome, "nome do ponto de venda")
    if any(p["nome"].lower() == nome.lower() for p in produto_dao.pontos(evento_id)):
        raise RegraNegocio(f"Já existe um ponto de venda chamado {nome}.")
    produto_dao.inserir_ponto(evento_id, nome)


def criar_produto(evento_id, nome, categoria, preco_texto, estoque_texto):
    nome = obrigatorio(nome, "nome do produto")
    if categoria not in CATEGORIAS:
        raise RegraNegocio("Escolha a categoria do produto.")
    produto_dao.inserir(evento_id, nome, categoria, _preco(preco_texto), _estoque(estoque_texto))


def atualizar_produto(evento_id, produto_id, preco_texto, estoque_texto):
    if produto_dao.buscar(produto_id, evento_id) is None:
        raise RegraNegocio("Produto não encontrado.")
    produto_dao.atualizar(produto_id, evento_id, _preco(preco_texto), _estoque(estoque_texto))


def _preco(texto):
    preco = para_centavos(texto)
    if preco <= 0:
        raise RegraNegocio("O preço precisa ser maior que zero.")
    return preco


def _estoque(texto):
    estoque = para_inteiro(texto, "estoque")
    if estoque < 0:
        raise RegraNegocio("O estoque não pode ser negativo.")
    return estoque
