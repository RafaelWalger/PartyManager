"""Tabela funcionario: membros da equipe de um evento e suas permissões."""
from app import banco

SELECT = """
    SELECT f.*, p.nome AS ponto_nome
    FROM funcionario f LEFT JOIN ponto_venda p ON p.id = f.ponto_id
"""


def listar(evento_id):
    return banco.listar(SELECT + " WHERE f.evento_id = %s ORDER BY f.ativo DESC, f.nome", evento_id)


def buscar(id, evento_id):
    return banco.buscar(SELECT + " WHERE f.id = %s AND f.evento_id = %s", id, evento_id)


def buscar_para_login(codigo_evento, usuario):
    """Usado no login da equipe: código do evento + usuário."""
    return banco.buscar(SELECT + """
        JOIN evento e ON e.id = f.evento_id
        WHERE e.codigo_acesso = %s AND f.usuario = %s
        """, codigo_evento.strip().upper(), usuario.strip().lower())


def existe_usuario(evento_id, usuario):
    return banco.valor("SELECT COUNT(*) FROM funcionario WHERE evento_id = %s AND usuario = %s",
                       evento_id, usuario.strip().lower()) > 0


def inserir(evento_id, ponto_id, nome, usuario, senha_hash, escanear, pdv, caixa, relatorios):
    return banco.inserir("""
        INSERT INTO funcionario (evento_id, ponto_id, nome, usuario, senha_hash,
                                 perm_escanear, perm_pdv, perm_caixa, perm_relatorios)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, evento_id, ponto_id, nome.strip(), usuario.strip().lower(), senha_hash,
        escanear, pdv, caixa, relatorios)


def atualizar_permissoes(id, evento_id, ponto_id, escanear, pdv, caixa, relatorios):
    banco.executar("""
        UPDATE funcionario
        SET ponto_id = %s, perm_escanear = %s, perm_pdv = %s, perm_caixa = %s, perm_relatorios = %s
        WHERE id = %s AND evento_id = %s
        """, ponto_id, escanear, pdv, caixa, relatorios, id, evento_id)


def alternar_ativo(id, evento_id):
    banco.executar("UPDATE funcionario SET ativo = NOT ativo WHERE id = %s AND evento_id = %s", id, evento_id)


def atualizar_senha(id, evento_id, senha_hash):
    banco.executar("UPDATE funcionario SET senha_hash = %s WHERE id = %s AND evento_id = %s",
                   senha_hash, id, evento_id)
