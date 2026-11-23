"""Lotes, emissão e validação de ingressos (RF04 e RF07)."""
from app.dao import ingresso_dao
from app.modelos import RegraNegocio
from app.utilidades import email_valido, gerar_codigo, obrigatorio, para_centavos, para_inteiro


def criar_lote(evento, nome, preco_texto, quantidade_texto):
    nome = obrigatorio(nome, "nome do lote")
    preco = para_centavos(preco_texto)
    quantidade = para_inteiro(quantidade_texto, "quantidade")
    if quantidade < 1:
        raise RegraNegocio("A quantidade precisa ser maior que zero.")
    ja_usado = ingresso_dao.total_de_lugares_em_lotes(evento["id"])
    if ja_usado + quantidade > evento["capacidade"]:
        raise RegraNegocio(f"Os lotes passariam da capacidade do evento ({evento['capacidade']}). "
                           f"Restam {evento['capacidade'] - ja_usado} lugares.")
    ingresso_dao.inserir_lote(evento["id"], nome, preco, quantidade)


def emitir(evento_id, lote_id, nome, email):
    """Emite o ingresso com um código único (que vira o QR Code). Devolve o ingresso."""
    nome = obrigatorio(nome, "nome do participante")
    email = (email or "").strip().lower() or None
    if email and not email_valido(email):
        raise RegraNegocio("E-mail do participante inválido.")
    lote = ingresso_dao.buscar_lote(lote_id, evento_id)
    if lote is None:
        raise RegraNegocio("Lote não encontrado.")
    if lote["restantes"] <= 0:
        raise RegraNegocio(f"O lote {lote['nome']} esgotou.")

    qr = "PM-" + gerar_codigo(8)
    while ingresso_dao.existe_qr(qr):
        qr = "PM-" + gerar_codigo(8)

    id = ingresso_dao.inserir(evento_id, lote_id, nome, email, qr, lote["preco"])
    return ingresso_dao.buscar(id, evento_id)


def validar(evento_id, codigo):
    """
    Lê o código do QR na portaria e libera a entrada uma única vez.
    Devolve (situacao, ingresso). situacao = 'ok', 'usado', 'cancelado' ou 'inexistente'.
    """
    limpo = (codigo or "").strip().upper()
    ingresso = ingresso_dao.buscar_por_qr(evento_id, limpo)
    if ingresso is None:
        return "inexistente", None
    if ingresso["status"] == "cancelado":
        return "cancelado", ingresso
    # O UPDATE só funciona se ainda estiver "valido": evita duas entradas com o mesmo QR
    situacao = "ok" if ingresso_dao.marcar_usado(ingresso["id"]) else "usado"
    return situacao, ingresso_dao.buscar(ingresso["id"], evento_id)


def cancelar(evento_id, ingresso_id):
    if not ingresso_dao.cancelar(ingresso_id, evento_id):
        raise RegraNegocio("Só dá para cancelar ingressos que ainda não foram usados.")
