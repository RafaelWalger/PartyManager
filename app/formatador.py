"""
Formatação usada nas páginas (registrada como filtros do Jinja).
No HTML:  {{ produto.preco | reais }}   ->   R$ 12,00
"""
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _milhar(numero_texto):
    """'1,234.56' (padrão americano) -> '1.234,56' (padrão brasileiro)."""
    return numero_texto.replace(",", "X").replace(".", ",").replace("X", ".")


def reais(centavos):
    """1250 -> 'R$ 12,50'"""
    centavos = centavos or 0
    sinal = "-" if centavos < 0 else ""
    return f"{sinal}R$ {_milhar(f'{abs(centavos) / 100:,.2f}')}"


def valor(centavos):
    """1250 -> '12,50' (para preencher campos de formulário)"""
    return f"{(centavos or 0) / 100:.2f}".replace(".", ",")


def numero(n):
    """1500 -> '1.500'"""
    return _milhar(f"{n or 0:,}")


def _local(d):
    """Datas gravadas com fuso (criado_em, usado_em) são mostradas no horário de Brasília."""
    if d is None:
        return None
    return d.astimezone(FUSO) if d.tzinfo else d


def data_hora(d):
    d = _local(d)
    return "—" if d is None else d.strftime("%d/%m/%Y às %H:%M")


def data(d):
    d = _local(d)
    return "—" if d is None else f"{d.day:02d} de {MESES[d.month - 1]} de {d.year}"


def curta(d):
    d = _local(d)
    return "—" if d is None else d.strftime("%d/%m %H:%M")


def hora(d):
    d = _local(d)
    return "—" if d is None else d.strftime("%H:%M")


def input_data(d):
    """Formato do campo <input type="datetime-local">."""
    return "" if d is None else _local(d).strftime("%Y-%m-%dT%H:%M")


def pct(parte, total):
    """Porcentagem inteira de parte/total, limitada entre 0 e 100."""
    if not total or total <= 0:
        return 0
    return max(0, min(100, round((parte or 0) * 100 / total)))


def tipo_transacao(tipo):
    return {"debito": "Compra", "recarga": "Recarga", "estorno": "Estorno"}.get(tipo, tipo)


def categoria(cat):
    return {"bebida": "Bebida", "comida": "Comida", "loja": "Loja"}.get(cat, cat)


def primeiro_nome(nome):
    return (nome or "").split(" ")[0]


def registrar(app):
    """Deixa as funções acima disponíveis nos templates."""
    for funcao in (reais, valor, numero, data_hora, data, curta, hora, input_data,
                   tipo_transacao, categoria, primeiro_nome):
        app.add_template_filter(funcao)
    app.add_template_global(pct)
