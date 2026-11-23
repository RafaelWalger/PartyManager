"""Gestão da equipe e das permissões (RF08)."""
import re

from app.dao import funcionario_dao, produto_dao
from app.modelos import RegraNegocio, plano_por_codigo
from app.seguranca import gerar_hash
from app.utilidades import obrigatorio


def criar(org, evento_id, nome, usuario, senha, ponto_id, escanear, pdv, caixa, relatorios):
    plano = plano_por_codigo(org["plano"])
    if plano.max_equipe is not None and len(funcionario_dao.listar(evento_id)) >= plano.max_equipe:
        raise RegraNegocio(f"Seu plano permite até {plano.max_equipe} pessoas na equipe por evento.")
    nome = obrigatorio(nome, "nome")
    usuario = obrigatorio(usuario, "usuário").lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,30}", usuario):
        raise RegraNegocio("O usuário deve ter de 3 a 30 letras minúsculas, números, ponto ou traço.")
    _validar_senha(senha)
    if funcionario_dao.existe_usuario(evento_id, usuario):
        raise RegraNegocio(f'Já existe alguém com o usuário "{usuario}" neste evento.')
    if not (escanear or pdv or caixa or relatorios):
        raise RegraNegocio("Marque pelo menos uma permissão.")
    funcionario_dao.inserir(evento_id, _ponto_valido(ponto_id, evento_id), nome, usuario, gerar_hash(senha),
                            escanear, pdv, caixa, relatorios)


def atualizar_permissoes(evento_id, funcionario_id, ponto_id, escanear, pdv, caixa, relatorios):
    if funcionario_dao.buscar(funcionario_id, evento_id) is None:
        raise RegraNegocio("Pessoa não encontrada.")
    funcionario_dao.atualizar_permissoes(funcionario_id, evento_id, _ponto_valido(ponto_id, evento_id),
                                         escanear, pdv, caixa, relatorios)


def redefinir_senha(evento_id, funcionario_id, senha):
    _validar_senha(senha)
    funcionario_dao.atualizar_senha(funcionario_id, evento_id, gerar_hash(senha))


def _ponto_valido(ponto_id, evento_id):
    """Só aceita ponto de venda do próprio evento (ou nenhum)."""
    if ponto_id is None:
        return None
    ponto = produto_dao.buscar_ponto(ponto_id, evento_id)
    return ponto["id"] if ponto else None


def _validar_senha(senha):
    if senha is None or len(senha) < 6:
        raise RegraNegocio("A senha da equipe precisa ter pelo menos 6 caracteres.")
    if len(senha.encode("utf-8")) > 72:
        raise RegraNegocio("A senha pode ter no máximo 72 caracteres.")
