"""Testes de integração para cobrinha.jogo: entrada de teclado e o laço de colisões.

Os testes de ``rodar_jogo`` simulam o avanço real de tempo (``time.sleep``)
porque a lógica do jogo usa um passo fixo baseado no relógio do pygame; sem
esse avanço, a cobra nunca chega a se mover de fato.
"""
import asyncio
import time

import pygame
import pytest

from cobrinha import config, entidades, jogo


def _fake_event_get_quit_apos(max_chamadas, sleep=0.02):
    """Cria uma função fake para pygame.event.get que "aperta" QUIT após N chamadas.

    Usada apenas como rede de segurança para não deixar um teste travar para
    sempre caso a cobra sobreviva mais do que o esperado.
    """
    contador = {"n": 0}

    def fake():
        contador["n"] += 1
        time.sleep(sleep)
        if contador["n"] > max_chamadas:
            return [pygame.event.Event(pygame.QUIT)]
        return []

    return fake


@pytest.fixture(autouse=True)
def resetar_config(monkeypatch):
    """Garante que cada teste comece com uma configuração conhecida e não persista nada em disco."""
    monkeypatch.setitem(config.CONFIG, "parede_atravessavel", False)
    monkeypatch.setitem(config.CONFIG, "dificuldade", "Fácil")
    monkeypatch.setitem(config.CONFIG, "modo_jogo", "1 Jogador")
    monkeypatch.setitem(config.CONFIG, "mapa_personalizado", False)


def test_aplicar_tecla_direcao_um_jogador():
    cobra = entidades.criar_cobra((100, 100), (config.TAMANHO_BLOCO, 0), "jogador1")
    jogo.aplicar_tecla_direcao(pygame.K_UP, "1 Jogador", [cobra])
    assert cobra.proxima_direcao == (0, -config.TAMANHO_BLOCO)


def test_aplicar_tecla_direcao_nao_permite_reverter():
    cobra = entidades.criar_cobra((100, 100), (config.TAMANHO_BLOCO, 0), "jogador1")
    # indo para a direita, tentar ir para a esquerda (reverter) deve ser ignorado
    jogo.aplicar_tecla_direcao(pygame.K_LEFT, "1 Jogador", [cobra])
    assert cobra.proxima_direcao == (config.TAMANHO_BLOCO, 0)


def test_aplicar_tecla_direcao_dois_jogadores_wasd_e_setas():
    jogador1 = entidades.criar_cobra((100, 200), (config.TAMANHO_BLOCO, 0), "jogador1")
    jogador2 = entidades.criar_cobra((480, 200), (-config.TAMANHO_BLOCO, 0), "jogador2")
    cobras = [jogador1, jogador2]

    jogo.aplicar_tecla_direcao(pygame.K_w, "2 Jogadores", cobras)
    assert jogador1.proxima_direcao == (0, -config.TAMANHO_BLOCO)
    assert jogador2.proxima_direcao == (-config.TAMANHO_BLOCO, 0)  # não mudou

    jogo.aplicar_tecla_direcao(pygame.K_DOWN, "2 Jogadores", cobras)
    assert jogador2.proxima_direcao == (0, config.TAMANHO_BLOCO)


def test_rodar_jogo_morre_na_parede(monkeypatch):
    monkeypatch.setattr(pygame, "event", pygame.event)
    monkeypatch.setattr(pygame.event, "get", _fake_event_get_quit_apos(300))

    cobras = asyncio.run(jogo.rodar_jogo(0, 0))

    assert len(cobras) == 1
    assert cobras[0].viva is False
    assert cobras[0].pontuacao == 0


def test_rodar_jogo_morre_no_obstaculo(monkeypatch):
    cabeca_inicial = (config.LARGURA // 2, config.ALTURA // 2)
    obstaculo_na_frente = (cabeca_inicial[0] + config.TAMANHO_BLOCO, cabeca_inicial[1])
    monkeypatch.setattr(jogo, "gerar_obstaculos", lambda qtd, ocupados: [obstaculo_na_frente])
    monkeypatch.setattr(pygame.event, "get", _fake_event_get_quit_apos(150))

    cobras = asyncio.run(jogo.rodar_jogo(0, 0))

    assert cobras[0].viva is False


def test_rodar_jogo_dois_jogadores_colisao_frontal(monkeypatch):
    monkeypatch.setitem(config.CONFIG, "modo_jogo", "2 Jogadores")
    monkeypatch.setattr(pygame.event, "get", _fake_event_get_quit_apos(300))

    cobras = asyncio.run(jogo.rodar_jogo(0, 0))

    assert len(cobras) == 2
    # as duas cobras começam na mesma linha se movendo uma em direção à outra:
    # o esperado é que colidam de frente e as duas morram
    assert cobras[0].viva is False
    assert cobras[1].viva is False
