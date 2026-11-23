"""Cadastro e edição de eventos (RF02)."""
from datetime import datetime

from app import banco
from app.dao import evento_dao, produto_dao
from app.modelos import RegraNegocio, plano_por_codigo
from app.utilidades import gerar_codigo, obrigatorio, para_inteiro

CLASSIFICACOES = ["Livre", "14 anos", "16 anos", "18 anos"]


def criar(org, nome, data_hora, local, classificacao, capacidade_texto):
    """Cria o evento e devolve o id."""
    plano = plano_por_codigo(org["plano"])
    if plano.max_eventos is not None and evento_dao.contar_por_organizador(org["id"]) >= plano.max_eventos:
        raise RegraNegocio(f"Seu plano {plano.nome} permite até {plano.max_eventos} evento(s). "
                           "Troque de plano para criar mais.")
    d = _validar(plano, nome, data_hora, local, classificacao, capacidade_texto)

    codigo = gerar_codigo(6)
    while evento_dao.existe_codigo(codigo):
        codigo = gerar_codigo(6)

    with banco.transacao():
        id = evento_dao.inserir(org["id"], d["nome"], d["data_hora"], d["local"], d["classificacao"],
                                d["capacidade"], codigo)
        # Todo evento já nasce com um ponto de venda para facilitar o começo
        produto_dao.inserir_ponto(id, "Bar")
    return id


def editar(org, evento_id, nome, data_hora, local, classificacao, capacidade_texto):
    if evento_dao.buscar(evento_id, org["id"]) is None:
        raise RegraNegocio("Evento não encontrado.")
    d = _validar(plano_por_codigo(org["plano"]), nome, data_hora, local, classificacao, capacidade_texto)
    evento_dao.atualizar(evento_id, org["id"], d["nome"], d["data_hora"], d["local"], d["classificacao"],
                         d["capacidade"])


def _validar(plano, nome, data_hora, local, classificacao, capacidade_texto):
    nome = obrigatorio(nome, "nome do evento")
    local = obrigatorio(local, "local")
    try:
        quando = datetime.fromisoformat(obrigatorio(data_hora, "data e horário"))
    except ValueError:
        raise RegraNegocio("Data e horário inválidos.") from None
    capacidade = para_inteiro(capacidade_texto, "capacidade")
    if capacidade < 1:
        raise RegraNegocio("A capacidade precisa ser maior que zero.")
    if plano.max_capacidade is not None and capacidade > plano.max_capacidade:
        raise RegraNegocio(f"Seu plano permite até {plano.max_capacidade} pessoas por evento.")
    if classificacao not in CLASSIFICACOES:
        classificacao = "Livre"
    return {"nome": nome, "data_hora": quando, "local": local,
            "classificacao": classificacao, "capacidade": capacidade}
