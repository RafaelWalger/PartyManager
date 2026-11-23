"""Planos de assinatura, temas de cor e os erros "esperados" do sistema."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Plano:
    """Plano de assinatura. None = ilimitado. Preço em centavos por mês."""
    codigo: str
    nome: str
    preco: int
    max_eventos: int | None
    max_capacidade: int | None
    max_equipe: int | None


PLANOS = [
    Plano("basico", "Básico", 4900, 1, 300, 3),
    Plano("profissional", "Profissional", 12900, 3, 1500, 15),
    Plano("festival", "Festival", 29900, None, None, None),
]


def plano_por_codigo(codigo):
    for plano in PLANOS:
        if plano.codigo == codigo:
            return plano
    return PLANOS[0]


@dataclass(frozen=True)
class Tema:
    """Preset de cores da interface (o CSS de cada um fica em public/css/temas.css)."""
    codigo: str
    nome: str


TEMAS = [
    Tema("neon", "Roxo neon"),
    Tema("reveillon", "Réveillon"),
    Tema("carnaval", "Carnaval"),
    Tema("por-do-sol", "Pôr do sol"),
    Tema("aurora", "Aurora"),
]


def tema_existe(codigo):
    return any(t.codigo == codigo for t in TEMAS)


class RegraNegocio(Exception):
    """Erro "esperado" (saldo insuficiente, ingresso já usado...). A mensagem vai para a tela."""


class SemEvento(Exception):
    """O organizador abriu uma tela que precisa de evento, mas ainda não criou nenhum."""

    def __init__(self):
        super().__init__("Crie seu primeiro evento para começar.")
