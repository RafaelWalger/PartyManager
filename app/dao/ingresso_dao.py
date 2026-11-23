"""Tabelas lote e ingresso."""
from app import banco

# "vendidos" e "restantes" são calculados na consulta (não são colunas)
SELECT_LOTE = """
    SELECT l.*,
           (SELECT COUNT(*) FROM ingresso i WHERE i.lote_id = l.id AND i.status <> 'cancelado') AS vendidos,
           GREATEST(0, l.quantidade - (SELECT COUNT(*) FROM ingresso i
                                       WHERE i.lote_id = l.id AND i.status <> 'cancelado')) AS restantes
    FROM lote l
"""

SELECT_INGRESSO = """
    SELECT i.*, l.nome AS lote_nome
    FROM ingresso i JOIN lote l ON l.id = i.lote_id
"""


# ------------------------------------------------------------ Lotes
def lotes(evento_id):
    return banco.listar(SELECT_LOTE + " WHERE l.evento_id = %s ORDER BY l.preco DESC", evento_id)


def buscar_lote(id, evento_id):
    return banco.buscar(SELECT_LOTE + " WHERE l.id = %s AND l.evento_id = %s", id, evento_id)


def inserir_lote(evento_id, nome, preco, quantidade):
    return banco.inserir("INSERT INTO lote (evento_id, nome, preco, quantidade) VALUES (%s, %s, %s, %s) RETURNING id",
                         evento_id, nome.strip(), preco, quantidade)


def total_de_lugares_em_lotes(evento_id):
    return banco.valor("SELECT COALESCE(SUM(quantidade), 0) FROM lote WHERE evento_id = %s", evento_id)


# ------------------------------------------------------------ Ingressos
def listar(evento_id, busca):
    return banco.listar(SELECT_INGRESSO + """
        WHERE i.evento_id = %s AND (i.nome_participante || ' ' || i.qr_code) ILIKE %s
        ORDER BY i.criado_em DESC
        LIMIT 200
        """, evento_id, "%" + (busca or "").strip() + "%")


def buscar(id, evento_id):
    return banco.buscar(SELECT_INGRESSO + " WHERE i.id = %s AND i.evento_id = %s", id, evento_id)


def buscar_por_qr(evento_id, qr_code):
    return banco.buscar(SELECT_INGRESSO + " WHERE i.evento_id = %s AND i.qr_code = %s", evento_id, qr_code)


def existe_qr(qr_code):
    return banco.valor("SELECT COUNT(*) FROM ingresso WHERE qr_code = %s", qr_code) > 0


def inserir(evento_id, lote_id, nome, email, qr_code, valor):
    return banco.inserir("""
        INSERT INTO ingresso (evento_id, lote_id, nome_participante, email_participante, qr_code, valor)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """, evento_id, lote_id, nome.strip(), email, qr_code, valor)


def marcar_usado(id):
    """Marca como usado só se ainda estiver válido. Devolve True se conseguiu."""
    return banco.executar("""
        UPDATE ingresso SET status = 'usado', usado_em = now()
        WHERE id = %s AND status = 'valido'
        """, id) == 1


def cancelar(id, evento_id):
    return banco.executar("""
        UPDATE ingresso SET status = 'cancelado'
        WHERE id = %s AND evento_id = %s AND status = 'valido'
        """, id, evento_id) == 1


def contar(evento_id, status):
    return banco.valor("SELECT COUNT(*) FROM ingresso WHERE evento_id = %s AND status = %s", evento_id, status)
