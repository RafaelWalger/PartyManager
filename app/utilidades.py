"""Funções pequenas usadas em vários lugares."""
import re
import secrets
from decimal import ROUND_HALF_UP, Decimal

from app.modelos import RegraNegocio

# Sem 0/O e 1/I, para ninguém confundir ao digitar
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def gerar_codigo(tamanho):
    return "".join(secrets.choice(ALFABETO) for _ in range(tamanho))


def para_centavos(texto):
    """'12,50' / '12.50' / 'R$ 1.234,56' -> centavos. Lança erro se for inválido."""
    if texto is None or not texto.strip():
        raise RegraNegocio("Informe um valor.")
    limpo = texto.replace("R$", "").replace(" ", "").replace(" ", "").strip()
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d{1,2})?", limpo):
        raise RegraNegocio("Valor inválido: use o formato 12,50.")
    return int((Decimal(limpo) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def para_inteiro(texto, campo):
    """'300' -> 300. Lança erro com o nome do campo se não for número."""
    try:
        return int(obrigatorio(texto, campo))
    except ValueError:
        raise RegraNegocio(f"Número inválido no campo {campo}.") from None


def somente_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def cpf_valido(cpf):
    """Confere os dois dígitos verificadores do CPF."""
    n = somente_digitos(cpf)
    if len(n) != 11 or len(set(n)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(n[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10 % 11) % 10
        if digito != int(n[tamanho]):
            return False
    return True


def email_valido(email):
    return email is not None and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()) is not None


def normalizar_uid(uid):
    """
    Leitores NFC "digitam" o UID de formas diferentes (04a23f, 04:A2:3F, 04 A2 3F).
    Aqui tudo vira o mesmo formato: 04:A2:3F.
    """
    hexa = re.sub(r"[^0-9A-Fa-f]", "", uid or "").upper()
    return ":".join(hexa[i:i + 2] for i in range(0, len(hexa), 2))


def obrigatorio(valor, campo):
    if valor is None or not str(valor).strip():
        raise RegraNegocio(f"Preencha o campo {campo}.")
    return str(valor).strip()
