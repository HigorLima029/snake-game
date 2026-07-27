"""Geração e controle dos efeitos sonoros do jogo.

Os sons são gerados na hora (ondas senoidais simples), sem precisar de
nenhum arquivo de áudio externo.
"""
from __future__ import annotations

import numpy as np
import pygame

pygame.mixer.init()


def gerar_tom(
    frequencia: float, duracao: float = 0.12, volume: float = 0.3, taxa: int = 44100
) -> pygame.mixer.Sound:
    n_amostras = int(taxa * duracao)
    t = np.linspace(0, duracao, n_amostras, False)
    onda = np.sin(frequencia * t * 2 * np.pi)
    envelope = np.linspace(1, 0, n_amostras)  # evita "clique" no final do som
    onda = (onda * envelope * volume * 32767).astype(np.int16)
    estereo = np.column_stack((onda, onda))
    return pygame.sndarray.make_sound(np.ascontiguousarray(estereo))


SOM_COMER: pygame.mixer.Sound = gerar_tom(880, duracao=0.09, volume=0.35)
SOM_COLIDIR: pygame.mixer.Sound = gerar_tom(140, duracao=0.35, volume=0.4)
SOM_SELECIONAR: pygame.mixer.Sound = gerar_tom(600, duracao=0.06, volume=0.25)


def aplicar_volume(volume: float) -> None:
    """Define o volume (0.0 a 1.0) em todos os efeitos sonoros do jogo."""
    for som in (SOM_COMER, SOM_COLIDIR, SOM_SELECIONAR):
        som.set_volume(volume)
