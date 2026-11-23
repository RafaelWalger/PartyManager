"""Gera o QR Code do ingresso como imagem SVG (fica nítido em qualquer tamanho e na impressão)."""
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def svg(texto):
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    matriz = qr.get_matrix()   # lista de linhas; True = quadradinho preto (já inclui a borda)

    tamanho = len(matriz)
    caminho = "".join(f"M{x} {y}h1v1h-1z"
                      for y, linha in enumerate(matriz)
                      for x, preto in enumerate(linha) if preto)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tamanho} {tamanho}" '
            f'shape-rendering="crispEdges">\n'
            f'<rect width="100%" height="100%" fill="#ffffff"/>\n'
            f'<path fill="#000000" d="{caminho}"/>\n'
            f'</svg>\n')
