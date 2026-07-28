"""Configuração compartilhada dos testes (pytest).

Precisa rodar ANTES de qualquer import do pacote ``cobrinha``, porque
``cobrinha.config`` chama ``pygame.init()`` e ``cobrinha.sons`` chama
``pygame.mixer.init()`` assim que são importados — sem um driver de
vídeo/áudio "dummy", isso falharia em uma máquina sem tela (ex.: CI).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Garante que "import cobrinha" funcione independente de onde o pytest for
# executado (adiciona a raiz do projeto, onde este arquivo está, ao sys.path).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
