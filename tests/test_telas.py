"""Testes para cobrinha.telas: tradução de eventos de gamepad e desenho."""
import pygame

from cobrinha import config, entidades, telas


def test_tecla_virtual_hat_direcoes():
    assert telas.tecla_virtual_do_joystick(
        pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1))
    ) == pygame.K_UP
    assert telas.tecla_virtual_do_joystick(
        pygame.event.Event(pygame.JOYHATMOTION, value=(0, -1))
    ) == pygame.K_DOWN
    assert telas.tecla_virtual_do_joystick(
        pygame.event.Event(pygame.JOYHATMOTION, value=(-1, 0))
    ) == pygame.K_LEFT
    assert telas.tecla_virtual_do_joystick(
        pygame.event.Event(pygame.JOYHATMOTION, value=(1, 0))
    ) == pygame.K_RIGHT


def test_tecla_virtual_eixo_analogico_acima_do_limiar():
    evento_esquerda = pygame.event.Event(pygame.JOYAXISMOTION, axis=0, value=-0.8)
    evento_direita = pygame.event.Event(pygame.JOYAXISMOTION, axis=0, value=0.8)
    assert telas.tecla_virtual_do_joystick(evento_esquerda) == pygame.K_LEFT
    assert telas.tecla_virtual_do_joystick(evento_direita) == pygame.K_RIGHT


def test_tecla_virtual_eixo_analogico_abaixo_do_limiar_e_ignorado():
    evento_fraco = pygame.event.Event(pygame.JOYAXISMOTION, axis=0, value=0.1)
    assert telas.tecla_virtual_do_joystick(evento_fraco) is None


def test_tecla_virtual_botoes():
    evento_a = pygame.event.Event(pygame.JOYBUTTONDOWN, button=0)
    evento_b = pygame.event.Event(pygame.JOYBUTTONDOWN, button=1)
    assert telas.tecla_virtual_do_joystick(evento_a) == pygame.K_RETURN
    assert telas.tecla_virtual_do_joystick(evento_b) == pygame.K_ESCAPE


def test_tecla_virtual_evento_de_teclado_retorna_none():
    # tecla_virtual_do_joystick só entende eventos de joystick;
    # eventos de teclado devem ser tratados separadamente (evento.key)
    evento_teclado = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
    assert telas.tecla_virtual_do_joystick(evento_teclado) is None


def test_desenhar_jogo_nao_lanca_excecao_com_sprites():
    cobra = entidades.criar_cobra((100, 100), (config.TAMANHO_BLOCO, 0), "jogador1")
    cobra.corpo = [(100, 100), (80, 100), (60, 100)]
    cobra.corpo_anterior = list(cobra.corpo)

    # não deve levantar exceção para nenhuma direção da cabeça
    for direcao in [(0, -config.TAMANHO_BLOCO), (0, config.TAMANHO_BLOCO),
                    (-config.TAMANHO_BLOCO, 0), (config.TAMANHO_BLOCO, 0)]:
        cobra.direcao = direcao
        telas.desenhar_jogo(
            config.TEMAS[0], [cobra], 1.0, (200, 200), False, [(300, 300)],
            0, 8, 1, 0, [],
        )
