"""
Ponto de entrada no Vercel. O vercel.json manda toda requisição que não é
arquivo de public/ (css, js, fontes...) para cá, e o Vercel roda o "app" abaixo.
As variáveis SECRET_KEY e DATABASE_URL são configuradas no painel do Vercel.
"""
import os
import sys

# Deixa a pasta do projeto no caminho de importação, para achar o pacote "app"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import criar_app  # noqa: E402

app = criar_app()
