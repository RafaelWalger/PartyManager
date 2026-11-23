"""Consultas de resumo usadas nos relatórios. Valores em centavos."""
from app import banco

# Soma dos débitos menos os estornos (venda líquida)
VENDA_LIQUIDA = "SUM(CASE t.tipo WHEN 'debito' THEN t.valor WHEN 'estorno' THEN -t.valor ELSE 0 END)"


def ingressos_vendidos(evento_id):
    return banco.valor("SELECT COUNT(*) FROM ingresso WHERE evento_id = %s AND status <> 'cancelado'", evento_id)


def entradas(evento_id):
    return banco.valor("SELECT COUNT(*) FROM ingresso WHERE evento_id = %s AND status = 'usado'", evento_id)


def faturamento_ingressos(evento_id):
    return banco.valor("SELECT COALESCE(SUM(valor), 0) FROM ingresso WHERE evento_id = %s AND status <> 'cancelado'",
                       evento_id)


def vendas_liquidas(evento_id):
    return banco.valor("SELECT COALESCE(" + VENDA_LIQUIDA + ", 0) FROM transacao t "
                       "JOIN cartao_saldo c ON c.id = t.cartao_id WHERE c.evento_id = %s", evento_id)


def recargas(evento_id):
    return banco.valor("SELECT COALESCE(SUM(t.valor), 0) FROM transacao t JOIN cartao_saldo c ON c.id = t.cartao_id "
                       "WHERE c.evento_id = %s AND t.tipo = 'recarga'", evento_id)


def saldo_nas_pulseiras(evento_id):
    return banco.valor("SELECT COALESCE(SUM(saldo), 0) FROM cartao_saldo WHERE evento_id = %s", evento_id)


def pulseiras_ativas(evento_id):
    return banco.valor("SELECT COUNT(*) FROM cartao_saldo WHERE evento_id = %s AND ativo", evento_id)


def vendas_por_ponto(evento_id):
    return banco.listar("""
        SELECT p.nome AS rotulo, COALESCE(""" + VENDA_LIQUIDA + """, 0) AS valor
        FROM ponto_venda p
        LEFT JOIN transacao t ON t.ponto_id = p.id
        WHERE p.evento_id = %s
        GROUP BY p.id, p.nome
        ORDER BY valor DESC
        """, evento_id)


def ingressos_por_lote(evento_id):
    return banco.listar("""
        SELECT l.nome AS rotulo, COUNT(i.id) AS valor
        FROM lote l
        LEFT JOIN ingresso i ON i.lote_id = l.id AND i.status <> 'cancelado'
        WHERE l.evento_id = %s
        GROUP BY l.id, l.nome, l.preco
        ORDER BY l.preco DESC
        """, evento_id)


def produtos_mais_vendidos(evento_id, limite):
    """Produtos mais vendidos (ignora compras estornadas)."""
    return banco.listar("""
        SELECT pr.nome AS rotulo, SUM(it.quantidade) AS valor
        FROM item_transacao it
        JOIN produto pr ON pr.id = it.produto_id
        JOIN transacao t ON t.id = it.transacao_id
        WHERE pr.evento_id = %s
          AND NOT EXISTS (SELECT 1 FROM transacao e WHERE e.transacao_origem_id = t.id)
        GROUP BY pr.nome
        ORDER BY valor DESC
        LIMIT %s
        """, evento_id, limite)


def vendas_do_ponto(ponto_id):
    """Vendas de um ponto (usado no resumo da equipe)."""
    return banco.valor("SELECT COALESCE(" + VENDA_LIQUIDA + ", 0) FROM transacao t WHERE t.ponto_id = %s", ponto_id)


def vendas_do_funcionario(funcionario_id):
    return banco.valor("""
        SELECT COALESCE(SUM(t.valor), 0) FROM transacao t
        WHERE t.funcionario_id = %s AND t.tipo = 'debito'
          AND NOT EXISTS (SELECT 1 FROM transacao e WHERE e.transacao_origem_id = t.id)
        """, funcionario_id)
