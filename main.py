"""Ponto de entrada do Jogo da Cobrinha.

Funciona tanto para rodar localmente (``python main.py``) quanto para
empacotar com pygbag e rodar no navegador (que espera um ``main.py`` na
raiz do projeto com ``asyncio.run``).
"""
import asyncio

from cobrinha.jogo import main

if __name__ == "__main__":
    asyncio.run(main())
