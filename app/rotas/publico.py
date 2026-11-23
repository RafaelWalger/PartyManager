"""Páginas abertas: landing page, login, cadastro, login da equipe e /saude."""
from flask import Blueprint, redirect, render_template, request, url_for

from app import banco, seguranca
from app.modelos import RegraNegocio
from app.servicos import conta_servico

bp = Blueprint("publico", __name__)


@bp.get("/")
def inicio():
    return render_template("publico/inicio.html")


@bp.get("/termos")
def termos():
    return render_template("publico/termos.html")


# ------------------------------------------------------------ organizador
@bp.get("/entrar")
def entrar():
    return render_template("publico/entrar.html")


@bp.post("/entrar")
def entrar_enviar():
    try:
        org = seguranca.login_organizador(request.form.get("email"), request.form.get("senha"))
    except RegraNegocio as e:
        return render_template("publico/entrar.html", erro=str(e), email=request.form.get("email", "")), 401
    seguranca.entrar(org["id"], org["nome"], "organizador")
    return redirect(url_for("organizador.painel"))


@bp.post("/sair")
def sair():
    seguranca.sair()
    return redirect(url_for("publico.entrar", saiu=1))


@bp.get("/cadastro")
def cadastro():
    return render_template("publico/cadastro.html", plano_escolhido=request.args.get("plano", "profissional"))


@bp.post("/cadastro")
def cadastrar():
    f = request.form
    try:
        if not f.get("aceite"):
            raise RegraNegocio("Você precisa aceitar os termos de uso e a política de privacidade.")
        id = conta_servico.cadastrar(f.get("nome"), f.get("cpf"), f.get("email"), f.get("senha"),
                                     f.get("confirmacao"), f.get("plano", "basico"))
    except RegraNegocio as e:
        # Volta para o formulário mantendo o que a pessoa digitou (menos as senhas)
        return render_template("publico/cadastro.html", erro=str(e), nome=f.get("nome"), cpf=f.get("cpf"),
                               email=f.get("email"), plano_escolhido=f.get("plano", "basico"))
    # Já entra na conta logo depois de criar
    seguranca.entrar(id, f.get("nome", "").strip(), "organizador")
    return redirect(url_for("organizador.eventos", bemvindo=1))


# ------------------------------------------------------------ equipe
@bp.get("/equipe/entrar")
def entrar_equipe():
    return render_template("publico/entrar-equipe.html", codigo=request.args.get("codigo", "").strip().upper())


@bp.post("/equipe/entrar")
def entrar_equipe_enviar():
    f = request.form
    try:
        func = seguranca.login_funcionario(f.get("codigo"), f.get("usuario"), f.get("senha"))
    except RegraNegocio as e:
        return render_template("publico/entrar-equipe.html", erro=str(e),
                               codigo=f.get("codigo", "").strip().upper()), 401
    seguranca.entrar(func["id"], func["nome"], "funcionario", func["evento_id"])
    return redirect(url_for("equipe.inicio"))


@bp.post("/equipe/sair")
def sair_equipe():
    seguranca.sair()
    return redirect(url_for("publico.entrar_equipe", saiu=1))


# ------------------------------------------------------------ saúde
@bp.get("/saude")
def saude():
    """Responde "ok" se o site E o banco estão funcionando."""
    try:
        banco.valor("SELECT 1")
        return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}
    except Exception:
        return "banco indisponível", 503, {"Content-Type": "text/plain; charset=utf-8"}
