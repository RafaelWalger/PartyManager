"""
Roda o PartyManager no seu PC:

    python executar.py

e abra http://localhost:8080. As configurações vêm do arquivo .env
(copie o .env.example para .env e preencha).
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()   # lê o .env e coloca os valores em os.environ
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from app import criar_app  # noqa: E402

app = criar_app()

if __name__ == "__main__":
    porta = int(os.environ.get("PORTA", "8080"))
    # debug=True recarrega sozinho quando você salva um arquivo (nunca use em produção)
    app.run(host="127.0.0.1", port=porta, debug=os.environ.get("DEBUG") == "1")
