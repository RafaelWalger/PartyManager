"""Cadastro e conta do organizador."""
import re

from app.dao import organizador_dao
from app.modelos import RegraNegocio, plano_por_codigo, tema_existe
from app.seguranca import gerar_hash, senha_confere
from app.utilidades import cpf_valido, email_valido, obrigatorio, somente_digitos


def cadastrar(nome, cpf, email, senha, confirmacao, plano):
    """Cria a conta e devolve o id do novo organizador."""
    nome = obrigatorio(nome, "nome")
    email = obrigatorio(email, "e-mail").lower()
    cpf_limpo = somente_digitos(cpf)

    if len(nome) < 3:
        raise RegraNegocio("Digite seu nome completo.")
    if not cpf_valido(cpf_limpo):
        raise RegraNegocio("CPF inválido.")
    if not email_valido(email):
        raise RegraNegocio("E-mail inválido.")
    validar_senha(senha, confirmacao)
    if organizador_dao.existe_email(email):
        raise RegraNegocio("Já existe uma conta com esse e-mail.")
    if organizador_dao.existe_cpf(cpf_limpo):
        raise RegraNegocio("Já existe uma conta com esse CPF.")

    return organizador_dao.inserir(nome, cpf_limpo, email, gerar_hash(senha), plano_por_codigo(plano).codigo)


def alterar_nome(id, nome):
    nome = obrigatorio(nome, "nome")
    if len(nome) < 3:
        raise RegraNegocio("Digite seu nome completo.")
    organizador_dao.atualizar_nome(id, nome)


def alterar_senha(id, atual, nova, confirmacao):
    org = organizador_dao.buscar_por_id(id)
    if not senha_confere(atual, org["senha_hash"]):
        raise RegraNegocio("A senha atual está incorreta.")
    validar_senha(nova, confirmacao)
    organizador_dao.atualizar_senha(id, gerar_hash(nova))


def alterar_aparencia(id, tema, modo):
    if not tema_existe(tema):
        tema = "neon"
    if modo != "claro":
        modo = "escuro"
    organizador_dao.atualizar_aparencia(id, tema, modo)


def validar_senha(senha, confirmacao):
    """Mínimo de 8 caracteres, com pelo menos uma letra e um número."""
    senha = senha or ""
    if len(senha) < 8 or not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise RegraNegocio("A senha precisa ter pelo menos 8 caracteres, com letras e números.")
    if len(senha.encode("utf-8")) > 72:     # limite do BCrypt
        raise RegraNegocio("A senha pode ter no máximo 72 caracteres.")
    if senha != confirmacao:
        raise RegraNegocio("As senhas não são iguais.")
