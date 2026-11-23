"""Tabela evento. A equipe entra usando o codigo_acesso."""
from app import banco


def listar_por_organizador(organizador_id):
    return banco.listar("SELECT * FROM evento WHERE organizador_id = %s ORDER BY data_hora DESC",
                        organizador_id)


def buscar(id, organizador_id):
    """Busca garantindo que o evento é desse organizador (ninguém vê evento de outro)."""
    return banco.buscar("SELECT * FROM evento WHERE id = %s AND organizador_id = %s", id, organizador_id)


def buscar_por_id(id):
    return banco.buscar("SELECT * FROM evento WHERE id = %s", id)


def contar_por_organizador(organizador_id):
    return banco.valor("SELECT COUNT(*) FROM evento WHERE organizador_id = %s", organizador_id)


def existe_codigo(codigo):
    return banco.valor("SELECT COUNT(*) FROM evento WHERE codigo_acesso = %s", codigo) > 0


def inserir(organizador_id, nome, data_hora, local, classificacao, capacidade, codigo):
    return banco.inserir("""
        INSERT INTO evento (organizador_id, nome, data_hora, local_evento,
                            classificacao, capacidade, codigo_acesso)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, organizador_id, nome.strip(), data_hora, local.strip(), classificacao, capacidade, codigo)


def atualizar(id, organizador_id, nome, data_hora, local, classificacao, capacidade):
    banco.executar("""
        UPDATE evento SET nome = %s, data_hora = %s, local_evento = %s, classificacao = %s, capacidade = %s
        WHERE id = %s AND organizador_id = %s
        """, nome.strip(), data_hora, local.strip(), classificacao, capacidade, id, organizador_id)
