"""Tabelas ponto_venda e produto."""
from app import banco


# ------------------------------------------------------------ Pontos de venda
def pontos(evento_id):
    return banco.listar("SELECT * FROM ponto_venda WHERE evento_id = %s ORDER BY nome", evento_id)


def buscar_ponto(id, evento_id):
    return banco.buscar("SELECT * FROM ponto_venda WHERE id = %s AND evento_id = %s", id, evento_id)


def inserir_ponto(evento_id, nome):
    return banco.inserir("INSERT INTO ponto_venda (evento_id, nome) VALUES (%s, %s) RETURNING id",
                         evento_id, nome.strip())


# ------------------------------------------------------------ Produtos
def produtos(evento_id, somente_ativos):
    filtro = " AND ativo" if somente_ativos else ""
    return banco.listar("SELECT * FROM produto WHERE evento_id = %s" + filtro + " ORDER BY categoria, nome",
                        evento_id)


def buscar(id, evento_id):
    return banco.buscar("SELECT * FROM produto WHERE id = %s AND evento_id = %s", id, evento_id)


def inserir(evento_id, nome, categoria, preco, estoque):
    return banco.inserir("""
        INSERT INTO produto (evento_id, nome, categoria, preco, estoque)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """, evento_id, nome.strip(), categoria, preco, estoque)


def atualizar(id, evento_id, preco, estoque):
    banco.executar("UPDATE produto SET preco = %s, estoque = %s WHERE id = %s AND evento_id = %s",
                   preco, estoque, id, evento_id)


def alternar_ativo(id, evento_id):
    banco.executar("UPDATE produto SET ativo = NOT ativo WHERE id = %s AND evento_id = %s", id, evento_id)


def baixar_estoque(id, quantidade):
    """Tira do estoque só se tiver quantidade suficiente. Devolve True se conseguiu."""
    return banco.executar("""
        UPDATE produto SET estoque = estoque - %s
        WHERE id = %s AND estoque >= %s AND ativo
        """, quantidade, id, quantidade) == 1


def devolver_estoque(id, quantidade):
    banco.executar("UPDATE produto SET estoque = estoque + %s WHERE id = %s", quantidade, id)
