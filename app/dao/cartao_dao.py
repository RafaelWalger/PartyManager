"""Pulseiras NFC (cartao_saldo), transações e itens das compras."""
from app import banco

SELECT_TRANSACAO = """
    SELECT t.*, c.uid_nfc, f.nome AS funcionario_nome, p.nome AS ponto_nome,
           EXISTS (SELECT 1 FROM transacao e WHERE e.transacao_origem_id = t.id) AS estornada,
           (SELECT string_agg(it.quantidade || 'x ' || pr.nome, ', ' ORDER BY pr.nome)
              FROM item_transacao it JOIN produto pr ON pr.id = it.produto_id
             WHERE it.transacao_id = t.id) AS itens
    FROM transacao t
    JOIN cartao_saldo c ON c.id = t.cartao_id
    LEFT JOIN funcionario f ON f.id = t.funcionario_id
    LEFT JOIN ponto_venda p ON p.id = t.ponto_id
"""


# ------------------------------------------------------------ Pulseiras
def listar(evento_id, busca):
    return banco.listar("""
        SELECT * FROM cartao_saldo
        WHERE evento_id = %s AND uid_nfc ILIKE %s
        ORDER BY id DESC
        LIMIT 200
        """, evento_id, "%" + (busca or "").strip() + "%")


def buscar_por_uid(evento_id, uid):
    return banco.buscar("SELECT * FROM cartao_saldo WHERE evento_id = %s AND uid_nfc = %s", evento_id, uid)


def buscar(id, evento_id):
    return banco.buscar("SELECT * FROM cartao_saldo WHERE id = %s AND evento_id = %s", id, evento_id)


def inserir(evento_id, uid):
    return banco.inserir("INSERT INTO cartao_saldo (evento_id, uid_nfc) VALUES (%s, %s) RETURNING id",
                         evento_id, uid)


def alternar_ativo(id, evento_id):
    banco.executar("UPDATE cartao_saldo SET ativo = NOT ativo WHERE id = %s AND evento_id = %s", id, evento_id)


def debitar(id, valor):
    """
    Debita só se a pulseira estiver ativa e tiver saldo. A condição fica no próprio
    UPDATE para que duas cobranças ao mesmo tempo nunca deixem o saldo negativo.
    """
    return banco.executar("""
        UPDATE cartao_saldo SET saldo = saldo - %s
        WHERE id = %s AND ativo AND saldo >= %s
        """, valor, id, valor) == 1


def creditar(id, valor):
    banco.executar("UPDATE cartao_saldo SET saldo = saldo + %s WHERE id = %s", valor, id)


# ------------------------------------------------------------ Transações
def inserir_transacao(cartao_id, funcionario_id, ponto_id, valor, tipo, forma_pagamento, origem_id):
    return banco.inserir("""
        INSERT INTO transacao (cartao_id, funcionario_id, ponto_id, valor, tipo,
                               forma_pagamento, transacao_origem_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, cartao_id, funcionario_id, ponto_id, valor, tipo, forma_pagamento, origem_id)


def inserir_item(transacao_id, item):
    banco.inserir("""
        INSERT INTO item_transacao (transacao_id, produto_id, quantidade, preco_unitario)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """, transacao_id, item["produto_id"], item["quantidade"], item["preco_unitario"])


def itens(transacao_id):
    return banco.listar("""
        SELECT it.produto_id, p.nome, it.preco_unitario, it.quantidade,
               it.preco_unitario * it.quantidade AS subtotal
        FROM item_transacao it JOIN produto p ON p.id = it.produto_id
        WHERE it.transacao_id = %s
        """, transacao_id)


def buscar_transacao(id, evento_id):
    return banco.buscar(SELECT_TRANSACAO + " WHERE t.id = %s AND c.evento_id = %s", id, evento_id)


def transacoes(evento_id, tipo, limite):
    """Filtro opcional por tipo ('debito', 'recarga', 'estorno' ou vazio = todos)."""
    if tipo:
        return banco.listar(SELECT_TRANSACAO + """
            WHERE c.evento_id = %s AND t.tipo = %s
            ORDER BY t.criado_em DESC, t.id DESC LIMIT %s
            """, evento_id, tipo, limite)
    return banco.listar(SELECT_TRANSACAO + """
        WHERE c.evento_id = %s
        ORDER BY t.criado_em DESC, t.id DESC LIMIT %s
        """, evento_id, limite)


def transacoes_do_cartao(cartao_id, limite):
    return banco.listar(SELECT_TRANSACAO + " WHERE t.cartao_id = %s ORDER BY t.criado_em DESC, t.id DESC LIMIT %s",
                        cartao_id, limite)


def transacoes_do_funcionario(funcionario_id, limite):
    return banco.listar(SELECT_TRANSACAO + " WHERE t.funcionario_id = %s ORDER BY t.criado_em DESC, t.id DESC LIMIT %s",
                        funcionario_id, limite)


def ja_estornada(transacao_id):
    return banco.valor("SELECT COUNT(*) FROM transacao WHERE transacao_origem_id = %s", transacao_id) > 0
