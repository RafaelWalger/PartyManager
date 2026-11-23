"""
PartyManager — monta o site Flask.

    criar_app()  é chamado pelo api/index.py (Vercel) e pelo executar.py (no PC).

Aqui ficam: configuração, registro das rotas (blueprints), dados que todo
template usa (tema, organizador logado, evento aberto...) e o tratamento de erros.
"""
import hashlib
import logging
import os
from datetime import timedelta
from urllib.parse import urlparse

from flask import Flask, flash, g, get_flashed_messages, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from app import banco, formatador, seguranca
from app.dao import evento_dao
from app.icones import icone
from app.modelos import PLANOS, TEMAS, RegraNegocio, SemEvento, plano_por_codigo

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = logging.getLogger("partymanager")


def criar_app():
    # Os arquivos de public/ (css, js, fontes, imagens) ficam na raiz do site: /css/style.css
    app = Flask(__name__, static_folder=os.path.join(PASTA_PROJETO, "public"), static_url_path="")

    chave = chave_secreta()
    if not chave or not banco.endereco_do_banco():
        raise RuntimeError("Configure SECRET_KEY e DATABASE_URL (veja o .env.example).")
    app.config.update(
        SECRET_KEY=chave,                             # assina o cookie da sessão
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),   # no Vercel o site é sempre HTTPS
        MAX_CONTENT_LENGTH=1024 * 1024,
    )

    from app.rotas import equipe, organizador, publico
    app.register_blueprint(publico.bp)
    app.register_blueprint(organizador.bp)
    app.register_blueprint(equipe.bp)

    app.before_request(seguranca.verificar_csrf)
    app.teardown_appcontext(banco.fechar_conexao)
    formatador.registrar(app)
    app.add_template_global(icone)
    app.add_template_global(seguranca.csrf_token)
    app.add_template_global(juntar_avisos)
    app.context_processor(dados_do_layout)
    registrar_erros(app)
    return app


def chave_secreta():
    """
    SECRET_KEY configurada à mão (no .env ou no Vercel). Se não existir, usa uma
    chave derivada da senha do banco criada pela integração Supabase do Vercel
    (POSTGRES_PASSWORD): ela é secreta e igual em todas as cópias do site.
    """
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    senha_do_banco = os.environ.get("POSTGRES_PASSWORD")
    if senha_do_banco:
        return hashlib.sha256(("partymanager-sessao:" + senha_do_banco).encode()).hexdigest()
    return None


def dados_do_layout():
    """Coloca em TODAS as páginas os dados que o layout usa."""
    dados = {"temas": TEMAS, "planos": PLANOS, "usuario": seguranca.usuario_logado(),
             "tema": "neon", "modo": "escuro", "aparencia_no_servidor": False}
    if "func" in g:   # área da equipe
        dados["func"] = g.func
        dados["evento"] = g.evento
    try:
        org = seguranca.organizador_atual()
    except Exception:   # banco fora do ar: a página de erro ainda precisa abrir
        log.exception("Não foi possível carregar o organizador")
        org = None
    if org:
        # Organizador: a aparência fica salva no banco. Visitante e equipe: no navegador.
        dados.update(org=org, plano=plano_por_codigo(org["plano"]), tema=org["tema"], modo=org["modo"],
                     aparencia_no_servidor=True, eventos=evento_dao.listar_por_organizador(org["id"]),
                     evento_atual=seguranca.evento_atual())
    return dados


def juntar_avisos(ok=None, erro=None, info=None):
    """Junta as mensagens passadas pela rota com as guardadas por flash() antes de um redirect."""
    avisos = {"ok": ok, "erro": erro, "info": info}
    for categoria, mensagem in get_flashed_messages(with_categories=True):
        if categoria in avisos and not avisos[categoria]:
            avisos[categoria] = mensagem
    return avisos


def pagina_anterior():
    """Usa só o caminho do "Referer" (nunca outro site), para evitar redirecionamento aberto."""
    endereco = urlparse(request.referrer or "")
    if not endereco.path.startswith("/"):
        return "/"
    return endereco.path + ("?" + endereco.query if endereco.query else "")


def registrar_erros(app):
    @app.errorhandler(SemEvento)
    def sem_evento(e):
        flash(str(e), "info")
        return redirect(url_for("organizador.eventos"))

    @app.errorhandler(RegraNegocio)
    def regra(e):
        """Erros "esperados" viram mensagem na tela. Ex.: "Saldo insuficiente"."""
        if request.method == "GET":
            # Página de erro genérica: o motivo fica só no log, não aparece para o usuário
            log.info("Erro ao abrir %s: %s", request.path, e)
            return render_template("error.html"), 404
        # Formulário (POST): volta para a mesma página mostrando a mensagem
        flash(str(e), "erro")
        return redirect(pagina_anterior())

    @app.errorhandler(HTTPException)
    def http(e):
        log.info("%s em %s", e.code, request.path)
        return render_template("error.html"), e.code

    @app.errorhandler(Exception)
    def inesperado(e):
        log.exception("Erro inesperado em %s", request.path)
        return render_template("error.html"), 500
