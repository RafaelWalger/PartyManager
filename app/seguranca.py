"""
Segurança do site. São DUAS "portas de entrada" separadas:

 1) /equipe/...      -> login com código do evento + usuário + senha (funcionário)
 2) /organizador/... -> login com e-mail + senha (organizador)

Quem está logado fica guardado na sessão do Flask: um cookie ASSINADO com a
SECRET_KEY (ninguém consegue alterar o conteúdo sem a chave). Isso funciona
no Vercel, onde o servidor não guarda nada na memória entre um acesso e outro.

Senhas são guardadas com BCrypt (nunca em texto puro) e todo formulário POST
precisa mandar o token CSRF ({{ m.csrf() }} nos templates).
"""
import hmac
import secrets
from functools import wraps

import bcrypt
from flask import abort, g, redirect, request, session, url_for

from app.dao import evento_dao, funcionario_dao, organizador_dao
from app.modelos import RegraNegocio, SemEvento

# Hash de uma senha qualquer: usado para o login demorar o mesmo tempo
# mesmo quando o e-mail não existe (assim ninguém descobre quais e-mails têm conta).
HASH_FALSO = bcrypt.hashpw(b"senha-que-ninguem-usa", bcrypt.gensalt(10)).decode()


# ------------------------------------------------------------ senhas
def gerar_hash(senha):
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(10)).decode()


def senha_confere(senha, senha_hash):
    try:
        return bcrypt.checkpw((senha or "").encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:   # senha com mais de 72 bytes ou hash inválido
        return False


# ------------------------------------------------------------ CSRF
def csrf_token():
    """Token secreto da sessão, colocado em todo formulário POST."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def verificar_csrf():
    """Roda antes de toda requisição: POST sem o token certo é recusado."""
    if request.method == "POST":
        enviado = request.form.get("_csrf", "")
        esperado = session.get("_csrf", "")
        if not esperado or not hmac.compare_digest(enviado, esperado):
            abort(400)


# ------------------------------------------------------------ quem está logado
def usuario_logado():
    """{'id', 'nome', 'tipo', 'evento_id'} ou None. tipo = 'organizador' ou 'funcionario'."""
    return session.get("usuario")


def entrar(id, nome, tipo, evento_id=None):
    """Guarda o usuário na sessão. Limpa a sessão antes (evita sequestro de sessão)."""
    session.clear()
    session.permanent = True
    session["usuario"] = {"id": id, "nome": nome, "tipo": tipo, "evento_id": evento_id}


def sair():
    session.clear()


def login_organizador(email, senha):
    """Confere e-mail + senha. Devolve o organizador ou lança RegraNegocio."""
    org = organizador_dao.buscar_por_email(email or "")
    hash_salvo = org["senha_hash"] if org else HASH_FALSO
    if not senha_confere(senha, hash_salvo) or org is None:
        raise RegraNegocio("E-mail ou senha incorretos.")
    return org


def login_funcionario(codigo, usuario, senha):
    """Confere código do evento + usuário + senha. Devolve o funcionário ou lança RegraNegocio."""
    codigo = (codigo or "").strip().upper()
    func = funcionario_dao.buscar_para_login(codigo, usuario or "") if codigo else None
    hash_salvo = func["senha_hash"] if func else HASH_FALSO
    if not senha_confere(senha, hash_salvo) or func is None:
        raise RegraNegocio("Código do evento, usuário ou senha incorretos.")
    if not func["ativo"]:
        raise RegraNegocio("Seu acesso foi desativado pelo organizador.")
    return func


# ------------------------------------------------------------ organizador
def exige_organizador(rota):
    """Decorador: a página só abre para organizador logado (senão vai para o login)."""
    @wraps(rota)
    def protegida(*args, **kwargs):
        usuario = usuario_logado()
        if not usuario or usuario["tipo"] != "organizador":
            return redirect(url_for("publico.entrar"))
        if organizador_atual() is None:     # conta apagada do banco
            sair()
            return redirect(url_for("publico.entrar"))
        return rota(*args, **kwargs)
    return protegida


def organizador_atual():
    """Organizador logado, lido do banco (uma vez por requisição)."""
    if "org" not in g:
        usuario = usuario_logado()
        g.org = None
        if usuario and usuario["tipo"] == "organizador":
            g.org = organizador_dao.buscar_por_id(usuario["id"])
    return g.org


def evento_atual():
    """Evento aberto no painel. Se nenhum foi escolhido, abre o mais recente."""
    org = organizador_atual()
    if org is None:
        return None
    escolhido = session.get("evento_atual_id")
    if escolhido:
        evento = evento_dao.buscar(escolhido, org["id"])
        if evento:
            return evento
    eventos = evento_dao.listar_por_organizador(org["id"])
    if not eventos:
        return None
    session["evento_atual_id"] = eventos[0]["id"]
    return eventos[0]


def exigir_evento():
    evento = evento_atual()
    if evento is None:
        raise SemEvento()
    return evento


def abrir_evento(evento_id):
    org = organizador_atual()
    if evento_dao.buscar(evento_id, org["id"]):
        session["evento_atual_id"] = evento_id


# ------------------------------------------------------------ equipe
def exige_funcionario(rota):
    """
    Decorador da área da equipe. Busca o funcionário de novo no banco a cada
    tela: se o organizador mudar permissões ou desativar o acesso, vale na hora.
    Deixa g.func e g.evento prontos para a rota e para o template.
    """
    @wraps(rota)
    def protegida(*args, **kwargs):
        usuario = usuario_logado()
        if not usuario or usuario["tipo"] != "funcionario":
            return redirect(url_for("publico.entrar_equipe"))
        func = funcionario_dao.buscar(usuario["id"], usuario["evento_id"])
        evento = evento_dao.buscar_por_id(usuario["evento_id"])
        if func is None or not func["ativo"] or evento is None:
            sair()
            return redirect(url_for("publico.entrar_equipe", desativado=1))
        g.func = func
        g.evento = evento
        return rota(*args, **kwargs)
    return protegida


def exigir_permissao(tem_permissao):
    if not tem_permissao:
        raise RegraNegocio("Você não tem permissão para essa função. Fale com o organizador.")
