"""
Conexão com o banco PostgreSQL (Supabase) e funções para rodar SQL puro.

Cada requisição abre UMA conexão (na primeira vez que precisa) e fecha no
final. No Vercel o site roda como "função" que liga e desliga sozinha, então
não dá para manter um grupo de conexões abertas como num servidor comum.

As consultas usam %s no lugar dos valores. Os valores vão separados e o
driver (psycopg) cuida de escapar tudo: isso evita SQL Injection.

Cada comando é gravado na hora (autocommit). Quando uma operação tem vários
passos que precisam dar certo juntos (ex.: venda), usamos:

    with banco.transacao():
        ...vários comandos...

Se qualquer passo lançar erro, o banco desfaz tudo (rollback).
"""
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg
from flask import g
from psycopg.rows import dict_row


def endereco_do_banco():
    """
    Endereço do banco: DATABASE_URL (configurada à mão, ex.: no .env) ou
    POSTGRES_URL (criada sozinha pela integração Supabase do Vercel).
    """
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        return None
    # A integração do Vercel acrescenta "supa=..." no endereço; o driver não conhece esse parâmetro
    partes = urlsplit(url)
    parametros = [(nome, valor) for nome, valor in parse_qsl(partes.query) if nome != "supa"]
    return urlunsplit(partes._replace(query=urlencode(parametros)))


def conexao():
    """Devolve a conexão da requisição atual (abre na primeira chamada)."""
    if "conexao" not in g:
        g.conexao = psycopg.connect(
            endereco_do_banco(),
            row_factory=dict_row,      # cada linha vira um dicionário: linha["nome"]
            autocommit=True,           # cada comando grava na hora, fora de transacao()
            prepare_threshold=None,    # necessário no pooler do Supabase (porta 6543)
            connect_timeout=10,
        )
    return g.conexao


def fechar_conexao(erro=None):
    """Chamado pelo Flask no fim de cada requisição."""
    con = g.pop("conexao", None)
    if con is not None:
        con.close()


def transacao():
    """Agrupa vários comandos: ou grava tudo, ou nada."""
    return conexao().transaction()


# ---------------------------------------------------------------- consultas
def listar(sql, *parametros):
    """Todas as linhas do SELECT, como lista de dicionários."""
    return conexao().execute(sql, parametros).fetchall()


def buscar(sql, *parametros):
    """Primeira linha do SELECT, ou None se não achou nada."""
    return conexao().execute(sql, parametros).fetchone()


def valor(sql, *parametros):
    """Primeiro campo da primeira linha. Ex.: SELECT COUNT(*) ..."""
    linha = buscar(sql, *parametros)
    return None if linha is None else next(iter(linha.values()))


def executar(sql, *parametros):
    """INSERT/UPDATE/DELETE. Devolve quantas linhas foram afetadas."""
    return conexao().execute(sql, parametros).rowcount


def inserir(sql, *parametros):
    """INSERT ... RETURNING id. Devolve o id gerado pelo banco."""
    return conexao().execute(sql, parametros).fetchone()["id"]
