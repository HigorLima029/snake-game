"""Entidades do jogo: cobra, comida, obstáculos, partículas e a IA do bot.

Este módulo contém apenas lógica "pura" (sem laços de eventos do pygame),
o que o torna o alvo mais fácil de testar com pytest.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple

import pygame

from . import config
from .config import Cor, Direcao, Posicao


@dataclass
class Cobra:
    """Estado de uma cobra (jogador ou bot) durante uma partida."""

    corpo: List[Posicao]
    corpo_anterior: List[Posicao]
    direcao: Direcao
    proxima_direcao: Direcao
    pontuacao: int = 0
    escudo_ate: int = 0  # timestamp (ms) até quando a cobra fica protegida
    viva: bool = True
    controlador: str = "jogador1"  # "jogador1", "jogador2" ou "bot"


def criar_cobra(posicao_inicial: Posicao, direcao_inicial: Direcao, controlador: str) -> Cobra:
    return Cobra(
        corpo=[posicao_inicial],
        corpo_anterior=[posicao_inicial],
        direcao=direcao_inicial,
        proxima_direcao=direcao_inicial,
        controlador=controlador,
    )


def gerar_posicao_livre(ocupados: Iterable[Posicao]) -> Posicao:
    ocupados_set = set(ocupados)
    while True:
        pos = (
            random.randrange(0, config.LARGURA, config.TAMANHO_BLOCO),
            random.randrange(0, config.ALTURA, config.TAMANHO_BLOCO),
        )
        if pos not in ocupados_set:
            return pos


def gerar_obstaculos(quantidade: int, ocupados: Iterable[Posicao]) -> List[Posicao]:
    obstaculos: List[Posicao] = []
    ocupados_atual = list(ocupados)
    for _ in range(quantidade):
        pos = gerar_posicao_livre(ocupados_atual)
        obstaculos.append(pos)
        ocupados_atual.append(pos)
    return obstaculos


def gerar_comida(ocupados: Iterable[Posicao]) -> Tuple[Posicao, bool]:
    pos = gerar_posicao_livre(ocupados)
    especial = random.random() < config.CHANCE_COMIDA_ESPECIAL
    return pos, especial


# ---------- Partículas (efeito visual ao comer) ----------
class Particula:
    def __init__(self, x: float, y: float, cor: Cor) -> None:
        angulo = random.uniform(0, math.tau)
        velocidade = random.uniform(60, 160)
        self.x = x
        self.y = y
        self.vx = math.cos(angulo) * velocidade
        self.vy = math.sin(angulo) * velocidade
        self.vida_total = random.uniform(0.3, 0.6)
        self.vida = self.vida_total
        self.cor = cor
        self.raio_base = random.uniform(2, 4)

    def atualizar(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt

    def viva(self) -> bool:
        return self.vida > 0

    def desenhar(self, superficie: pygame.Surface) -> None:
        fracao = max(0.0, self.vida / self.vida_total)
        raio = max(1, int(self.raio_base * fracao))
        pygame.draw.circle(superficie, self.cor, (int(self.x), int(self.y)), raio)


def criar_particulas(x: int, y: int, cor: Cor, quantidade: int = 14) -> List[Particula]:
    centro_x = x + config.TAMANHO_BLOCO // 2
    centro_y = y + config.TAMANHO_BLOCO // 2
    return [Particula(centro_x, centro_y, cor) for _ in range(quantidade)]


# ---------- IA do bot ----------
def oposto(direcao: Direcao) -> Direcao:
    return (-direcao[0], -direcao[1])


def escolher_direcao_bot(
    cabeca: Posicao,
    direcao_atual: Direcao,
    comida: Posicao,
    celulas_perigosas: Set[Posicao],
) -> Direcao:
    """Escolhe a próxima direção do bot: evita perigo imediato e persegue a comida."""
    candidatas = [d for d in config.DIRECOES if d != oposto(direcao_atual)]
    seguras: List[Tuple[Direcao, Posicao]] = []
    for direcao in candidatas:
        proximo = (cabeca[0] + direcao[0], cabeca[1] + direcao[1])
        if config.CONFIG["parede_atravessavel"]:
            proximo = (proximo[0] % config.LARGURA, proximo[1] % config.ALTURA)
        elif proximo[0] < 0 or proximo[0] >= config.LARGURA or proximo[1] < 0 or proximo[1] >= config.ALTURA:
            continue
        if proximo in celulas_perigosas:
            continue
        seguras.append((direcao, proximo))

    if not seguras:
        return candidatas[0] if candidatas else direcao_atual

    def distancia(pos: Posicao) -> int:
        return abs(pos[0] - comida[0]) + abs(pos[1] - comida[1])

    seguras.sort(key=lambda item: distancia(item[1]))
    return seguras[0][0]


# ---------- Fases ----------
def calcular_fase(pontuacao: int) -> int:
    return 1 + pontuacao // config.PONTOS_POR_FASE


def obstaculos_extra_da_fase(fase: int) -> int:
    return min((fase - 1) * config.OBSTACULOS_POR_FASE, config.OBSTACULOS_MAXIMOS_FASE)


def interpolar_posicao(origem: Posicao, destino: Posicao, progresso: float) -> Tuple[float, float]:
    """Interpola a posição visual de um segmento entre dois passos lógicos.

    Evita um "arrastão" visual quando a cobra atravessa de um lado ao outro
    da tela (parede atravessável): nesse caso, retorna o destino direto.
    """
    dx = destino[0] - origem[0]
    dy = destino[1] - origem[1]
    if abs(dx) > config.TAMANHO_BLOCO * 1.5 or abs(dy) > config.TAMANHO_BLOCO * 1.5:
        return destino
    return (origem[0] + dx * progresso, origem[1] + dy * progresso)
