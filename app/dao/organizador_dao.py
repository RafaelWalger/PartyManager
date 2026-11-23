"""Tabela organizador: quem contrata o plano e cria os eventos."""
from app import banco


def buscar_por_id(id):
    return banco.buscar("SELECT * FROM organizador WHERE id = %s", id)


def buscar_por_email(email):
    return banco.buscar("SELECT * FROM organizador WHERE email = %s", email.strip().lower())


def existe_email(email):
    return banco.valor("SELECT COUNT(*) FROM organizador WHERE email = %s", email.strip().lower()) > 0


def existe_cpf(cpf):
    return banco.valor("SELECT COUNT(*) FROM organizador WHERE cpf = %s", cpf) > 0


def inserir(nome, cpf, email, senha_hash, plano):
    return banco.inserir("""
        INSERT INTO organizador (nome, cpf, email, senha_hash, plano, status_assinatura)
        VALUES (%s, %s, %s, %s, %s, 'ativa')
        RETURNING id
        """, nome.strip(), cpf, email.strip().lower(), senha_hash, plano)


def atualizar_aparencia(id, tema, modo):
    banco.executar("UPDATE organizador SET tema = %s, modo = %s WHERE id = %s", tema, modo, id)


def atualizar_nome(id, nome):
    banco.executar("UPDATE organizador SET nome = %s WHERE id = %s", nome.strip(), id)


def atualizar_senha(id, senha_hash):
    banco.executar("UPDATE organizador SET senha_hash = %s WHERE id = %s", senha_hash, id)
