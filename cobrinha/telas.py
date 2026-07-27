"""Telas do jogo: menu, configurações, editor de mapa, ranking, pausa e fim.

Todas as telas com laço próprio são ``async def`` com ``await
asyncio.sleep(0)`` a cada quadro — necessário para rodar tanto localmente
quanto empacotado para o navegador via pygbag.
"""
from __future__ import annotations

import asyncio
import math
import sys
from typing import List

import pygame

from . import config, sons
from .config import Cor
from .entidades import Cobra, Particula, interpolar_posicao


def desenhar_texto(
    texto: str,
    fonte_usada: pygame.font.Font,
    cor: Cor,
    x: int,
    y: int,
    centralizado: bool = False,
) -> pygame.Rect:
    superficie = fonte_usada.render(texto, True, cor)
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    config.tela.blit(superficie, rect)
    return rect


def desenhar_jogo(
    tema: config.Tema,
    cobras: List[Cobra],
    progresso: float,
    comida: config.Posicao,
    comida_especial: bool,
    obstaculos: List[config.Posicao],
    recorde: int,
    velocidade_atual: int,
    fase_atual: int,
    aviso_fase_ate: int,
    particulas: List[Particula],
) -> None:
    tela = config.tela
    tela.fill(tema["fundo"])

    for x in range(0, config.LARGURA, config.TAMANHO_BLOCO):
        pygame.draw.line(tela, tema["grade"], (x, 0), (x, config.ALTURA))
    for y in range(0, config.ALTURA, config.TAMANHO_BLOCO):
        pygame.draw.line(tela, tema["grade"], (0, y), (config.LARGURA, y))

    for obstaculo in obstaculos:
        pygame.draw.rect(tela, (95, 95, 95), (*obstaculo, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO))
        pygame.draw.rect(tela, (60, 60, 60), (*obstaculo, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO), 2)

    if comida_especial:
        pulso = int(3 * math.sin(pygame.time.get_ticks() / 120))
        centro = (comida[0] + config.TAMANHO_BLOCO // 2, comida[1] + config.TAMANHO_BLOCO // 2)
        pygame.draw.circle(tela, config.DOURADO, centro, config.TAMANHO_BLOCO // 2 + 3 + pulso)
        pygame.draw.circle(tela, (255, 255, 200), centro, config.TAMANHO_BLOCO // 3)
    else:
        pygame.draw.rect(tela, tema["comida"], (*comida, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO))

    for particula in particulas:
        particula.desenhar(tela)

    agora = pygame.time.get_ticks()
    for indice_cobra, cobra in enumerate(cobras):
        cor_cabeca, cor_corpo = (
            (tema["cabeca"], tema["corpo"]) if indice_cobra == 0 else (config.COR_CABECA_2, config.COR_CORPO_2)
        )
        protegido = agora < cobra.escudo_ate
        for i, segmento_novo in enumerate(cobra.corpo):
            origem = cobra.corpo_anterior[i] if i < len(cobra.corpo_anterior) else segmento_novo
            x, y = interpolar_posicao(origem, segmento_novo, progresso)
            cor = cor_cabeca if i == 0 else cor_corpo
            if not cobra.viva:
                cor = (80, 80, 80)
            pygame.draw.rect(tela, cor, (x, y, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO))
            if protegido:
                pygame.draw.rect(tela, config.DOURADO, (x, y, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO), 2)

    pontuacao_max = max(c.pontuacao for c in cobras)

    if len(cobras) > 1:
        rotulo2 = "Bot" if cobras[1].controlador == "bot" else "Jogador 2"
        desenhar_texto(f"Jogador 1: {cobras[0].pontuacao}", config.fonte, config.BRANCO, 10, 10)
        desenhar_texto(f"{rotulo2}: {cobras[1].pontuacao}", config.fonte, (230, 140, 230), 10, 33)
    else:
        desenhar_texto(f"Pontuação: {cobras[0].pontuacao}", config.fonte, config.BRANCO, 10, 10)
        desenhar_texto(f"Recorde: {recorde}", config.fonte, config.BRANCO, 10, 33)

    desenhar_texto(f"Fase: {fase_atual}", config.fonte, (170, 170, 170), config.LARGURA - 80, 33)
    desenhar_texto("P/ESC: pausar", config.fonte, (150, 150, 150), config.LARGURA - 140, 10)

    if velocidade_atual >= config.VELOCIDADE_MAXIMA:
        desenhar_texto("Velocidade máxima!", config.fonte, config.AMARELO, 10, 58)
    else:
        pontos_restantes = config.PONTOS_POR_NIVEL - (pontuacao_max % config.PONTOS_POR_NIVEL)
        desenhar_texto(
            f"Próx. velocidade em {pontos_restantes} ponto(s)", config.fonte, (150, 150, 150), 10, 58
        )
        progresso_barra = 1 - (pontos_restantes / config.PONTOS_POR_NIVEL)
        largura_barra = 150
        pygame.draw.rect(tela, (60, 60, 60), (10, 82, largura_barra, 8))
        pygame.draw.rect(tela, config.AMARELO, (10, 82, int(largura_barra * progresso_barra), 8))

    if agora < aviso_fase_ate:
        desenhar_texto(
            f"Fase {fase_atual}!", config.fonte_grande, config.AMARELO,
            config.LARGURA // 2, config.ALTURA // 2 - 80, centralizado=True,
        )

    pygame.display.update()


async def menu_principal(indice_tema: int, recorde: int) -> int:
    opcoes = ["Jogar", "Tema", "Configurações", "Editor de Mapa", "Ranking", "Sair"]
    selecionado = 0

    while True:
        tema = config.TEMAS[indice_tema]
        config.tela.fill(config.PRETO)
        desenhar_texto("JOGO DA COBRINHA", config.fonte_grande, config.AMARELO, config.LARGURA // 2, 42, centralizado=True)
        desenhar_texto(
            f"Recorde: {recorde}   |   Dificuldade: {config.CONFIG['dificuldade']}   |   "
            f"Modo: {config.CONFIG['modo_jogo']}",
            config.fonte, (170, 170, 170), config.LARGURA // 2, 78, centralizado=True,
        )

        for i, opcao in enumerate(opcoes):
            cor = config.AMARELO if i == selecionado else config.BRANCO
            texto = opcao
            if opcao == "Tema":
                texto = f"< Tema: {tema['nome']} >"
            desenhar_texto(texto, config.fonte, cor, config.LARGURA // 2, 118 + i * 36, centralizado=True)

        desenhar_texto(
            "seta cima/baixo: navegar   esquerda/direita: trocar tema   Enter: confirmar",
            config.fonte, (150, 150, 150), config.LARGURA // 2, config.ALTURA - 15, centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    selecionado = (selecionado - 1) % len(opcoes)
                    sons.SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    selecionado = (selecionado + 1) % len(opcoes)
                    sons.SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_LEFT, pygame.K_a) and opcoes[selecionado] == "Tema":
                    indice_tema = (indice_tema - 1) % len(config.TEMAS)
                    sons.SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_RIGHT, pygame.K_d) and opcoes[selecionado] == "Tema":
                    indice_tema = (indice_tema + 1) % len(config.TEMAS)
                    sons.SOM_SELECIONAR.play()
                elif evento.key == pygame.K_RETURN:
                    if opcoes[selecionado] == "Jogar":
                        return indice_tema
                    elif opcoes[selecionado] == "Configurações":
                        await tela_configuracoes()
                    elif opcoes[selecionado] == "Editor de Mapa":
                        await tela_editor_mapa()
                    elif opcoes[selecionado] == "Ranking":
                        await tela_ranking()
                    elif opcoes[selecionado] == "Sair":
                        pygame.quit()
                        sys.exit()

        await asyncio.sleep(0)
        config.relogio.tick(30)


async def tela_configuracoes() -> None:
    opcoes = ["Volume", "Velocidade inicial", "Parede", "Dificuldade", "Modo", "Mapa", "Voltar"]
    selecionado = 0

    while True:
        config.tela.fill(config.PRETO)
        desenhar_texto("CONFIGURAÇÕES", config.fonte_grande, config.AMARELO, config.LARGURA // 2, 35, centralizado=True)

        for i, opcao in enumerate(opcoes):
            cor = config.AMARELO if i == selecionado else config.BRANCO
            if opcao == "Volume":
                texto = f"< Volume: {int(config.CONFIG['volume'] * 100)}% >"
            elif opcao == "Velocidade inicial":
                texto = f"< Velocidade inicial: {config.CONFIG['velocidade_inicial']} >"
            elif opcao == "Parede":
                estado = "Atravessável" if config.CONFIG["parede_atravessavel"] else "Sólida"
                texto = f"< Parede: {estado} >"
            elif opcao == "Dificuldade":
                texto = f"< Dificuldade: {config.CONFIG['dificuldade']} >"
            elif opcao == "Modo":
                texto = f"< Modo: {config.CONFIG['modo_jogo']} >"
            elif opcao == "Mapa":
                estado = "Personalizado" if config.CONFIG["mapa_personalizado"] else "Aleatório"
                texto = f"< Mapa: {estado} >"
            else:
                texto = opcao
            desenhar_texto(texto, config.fonte, cor, config.LARGURA // 2, 78 + i * 33, centralizado=True)

        desenhar_texto(
            "esquerda/direita: ajustar   Enter/ESC: voltar",
            config.fonte, (150, 150, 150), config.LARGURA // 2, config.ALTURA - 15, centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    selecionado = (selecionado - 1) % len(opcoes)
                    sons.SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    selecionado = (selecionado + 1) % len(opcoes)
                    sons.SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    direita = evento.key in (pygame.K_RIGHT, pygame.K_d)
                    opcao = opcoes[selecionado]
                    alterou = True
                    if opcao == "Volume":
                        delta = 0.1 if direita else -0.1
                        config.CONFIG["volume"] = round(min(max(config.CONFIG["volume"] + delta, 0.0), 1.0), 2)
                        sons.aplicar_volume(config.CONFIG["volume"])
                    elif opcao == "Velocidade inicial":
                        delta = 1 if direita else -1
                        config.CONFIG["velocidade_inicial"] = min(
                            max(config.CONFIG["velocidade_inicial"] + delta, config.VELOCIDADE_INICIAL_MIN),
                            config.VELOCIDADE_INICIAL_MAX,
                        )
                    elif opcao == "Parede":
                        config.CONFIG["parede_atravessavel"] = not config.CONFIG["parede_atravessavel"]
                    elif opcao == "Dificuldade":
                        idx = config.LISTA_DIFICULDADES.index(config.CONFIG["dificuldade"])
                        idx = (idx + (1 if direita else -1)) % len(config.LISTA_DIFICULDADES)
                        config.CONFIG["dificuldade"] = config.LISTA_DIFICULDADES[idx]
                    elif opcao == "Modo":
                        idx = config.MODOS_JOGO.index(config.CONFIG["modo_jogo"])
                        idx = (idx + (1 if direita else -1)) % len(config.MODOS_JOGO)
                        config.CONFIG["modo_jogo"] = config.MODOS_JOGO[idx]
                    elif opcao == "Mapa":
                        config.CONFIG["mapa_personalizado"] = not config.CONFIG["mapa_personalizado"]
                    else:
                        alterou = False
                    if alterou:
                        sons.SOM_SELECIONAR.play()
                        config.salvar_config()
                elif evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    if opcoes[selecionado] == "Voltar" or evento.key == pygame.K_ESCAPE:
                        return

        await asyncio.sleep(0)
        config.relogio.tick(30)


async def tela_editor_mapa() -> None:
    colunas = config.LARGURA // config.TAMANHO_BLOCO
    linhas = config.ALTURA // config.TAMANHO_BLOCO
    obstaculos = set(config.carregar_mapa_personalizado())
    cursor_x, cursor_y = colunas // 2, linhas // 2

    while True:
        config.tela.fill(config.PRETO)
        for x in range(0, config.LARGURA, config.TAMANHO_BLOCO):
            pygame.draw.line(config.tela, config.CINZA, (x, 0), (x, config.ALTURA))
        for y in range(0, config.ALTURA, config.TAMANHO_BLOCO):
            pygame.draw.line(config.tela, config.CINZA, (0, y), (config.LARGURA, y))

        for (ox, oy) in obstaculos:
            pygame.draw.rect(config.tela, (95, 95, 95), (ox, oy, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO))

        cursor_pos = (cursor_x * config.TAMANHO_BLOCO, cursor_y * config.TAMANHO_BLOCO)
        pygame.draw.rect(config.tela, config.AMARELO, (*cursor_pos, config.TAMANHO_BLOCO, config.TAMANHO_BLOCO), 3)

        desenhar_texto("EDITOR DE MAPA", config.fonte, config.AMARELO, config.LARGURA // 2, 16, centralizado=True)
        desenhar_texto(
            "setas: mover   espaço/enter: alternar obstáculo   C: limpar   S: salvar   ESC: cancelar",
            config.fonte, (150, 150, 150), config.LARGURA // 2, config.ALTURA - 12, centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    cursor_y = (cursor_y - 1) % linhas
                elif evento.key == pygame.K_DOWN:
                    cursor_y = (cursor_y + 1) % linhas
                elif evento.key == pygame.K_LEFT:
                    cursor_x = (cursor_x - 1) % colunas
                elif evento.key == pygame.K_RIGHT:
                    cursor_x = (cursor_x + 1) % colunas
                elif evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                    pos = (cursor_x * config.TAMANHO_BLOCO, cursor_y * config.TAMANHO_BLOCO)
                    if pos in obstaculos:
                        obstaculos.discard(pos)
                    else:
                        obstaculos.add(pos)
                    sons.SOM_SELECIONAR.play()
                elif evento.key == pygame.K_c:
                    obstaculos.clear()
                elif evento.key == pygame.K_s:
                    config.salvar_mapa_personalizado(sorted(obstaculos))
                    return
                elif evento.key == pygame.K_ESCAPE:
                    return

        await asyncio.sleep(0)
        config.relogio.tick(30)


async def tela_ranking() -> None:
    ranking = config.carregar_ranking()
    while True:
        config.tela.fill(config.PRETO)
        desenhar_texto("RANKING LOCAL", config.fonte_grande, config.AMARELO, config.LARGURA // 2, 36, centralizado=True)
        if not ranking:
            desenhar_texto(
                "Ainda não há pontuações registradas.", config.fonte, config.BRANCO,
                config.LARGURA // 2, 110, centralizado=True,
            )
        else:
            for i, registro in enumerate(ranking[:10]):
                texto = f"{i + 1}. {registro['nome']} — {registro['pontuacao']} pts"
                desenhar_texto(texto, config.fonte, config.BRANCO, config.LARGURA // 2, 85 + i * 27, centralizado=True)
        desenhar_texto(
            "Enter ou ESC: voltar", config.fonte, (150, 150, 150), config.LARGURA // 2, config.ALTURA - 15,
            centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                return

        await asyncio.sleep(0)
        config.relogio.tick(30)


async def tela_entrada_nome(pontuacao: int) -> str:
    nome = ""
    while True:
        config.tela.fill(config.PRETO)
        desenhar_texto(
            "Novo recorde no ranking!", config.fonte_grande, config.AMARELO, config.LARGURA // 2, 90, centralizado=True
        )
        desenhar_texto(f"Pontuação: {pontuacao}", config.fonte, config.BRANCO, config.LARGURA // 2, 140, centralizado=True)
        desenhar_texto("Digite seu nome:", config.fonte, config.BRANCO, config.LARGURA // 2, 180, centralizado=True)
        desenhar_texto(nome + "_", config.fonte_grande, config.AMARELO, config.LARGURA // 2, 220, centralizado=True)
        desenhar_texto(
            "Enter: confirmar   Backspace: apagar", config.fonte, (150, 150, 150),
            config.LARGURA // 2, config.ALTURA - 15, centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN and nome.strip():
                    return nome.strip()[:12]
                elif evento.key == pygame.K_BACKSPACE:
                    nome = nome[:-1]
                elif evento.unicode.isprintable() and len(nome) < 12:
                    nome += evento.unicode

        await asyncio.sleep(0)
        config.relogio.tick(30)


def tela_de_pausa() -> None:
    overlay = pygame.Surface((config.LARGURA, config.ALTURA))
    overlay.set_alpha(180)
    overlay.fill(config.PRETO)
    config.tela.blit(overlay, (0, 0))
    desenhar_texto(
        "PAUSADO", config.fonte_grande, config.AMARELO, config.LARGURA // 2, config.ALTURA // 2 - 20,
        centralizado=True,
    )
    desenhar_texto(
        "Pressione P ou ESC para continuar", config.fonte, config.BRANCO,
        config.LARGURA // 2, config.ALTURA // 2 + 30, centralizado=True,
    )
    pygame.display.update()


async def tela_de_fim(cobras: List[Cobra], modo_jogo: str, recorde: int) -> str:
    config.tela.fill(config.PRETO)
    desenhar_texto("Fim de jogo!", config.fonte_grande, (200, 40, 40), config.LARGURA // 2, 65, centralizado=True)

    if modo_jogo == "2 Jogadores":
        p1, p2 = cobras[0].pontuacao, cobras[1].pontuacao
        desenhar_texto(f"Jogador 1: {p1} pontos", config.fonte, config.BRANCO, config.LARGURA // 2, 130, centralizado=True)
        desenhar_texto(f"Jogador 2: {p2} pontos", config.fonte, config.BRANCO, config.LARGURA // 2, 158, centralizado=True)
        if p1 > p2:
            resultado = "Jogador 1 venceu!"
        elif p2 > p1:
            resultado = "Jogador 2 venceu!"
        else:
            resultado = "Empate!"
        desenhar_texto(resultado, config.fonte, config.AMARELO, config.LARGURA // 2, 195, centralizado=True)
    else:
        pontuacao = cobras[0].pontuacao
        desenhar_texto(f"Pontuação: {pontuacao}", config.fonte, config.BRANCO, config.LARGURA // 2, 130, centralizado=True)
        if pontuacao > recorde:
            desenhar_texto("Novo recorde!", config.fonte, config.AMARELO, config.LARGURA // 2, 160, centralizado=True)
        else:
            desenhar_texto(f"Recorde: {recorde}", config.fonte, config.BRANCO, config.LARGURA // 2, 160, centralizado=True)

    desenhar_texto(
        "R: jogar de novo    M: menu    Q: sair", config.fonte, (180, 180, 180),
        config.LARGURA // 2, config.ALTURA - 40, centralizado=True,
    )
    pygame.display.update()

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_r:
                    return "jogar"
                if evento.key == pygame.K_m:
                    return "menu"
                if evento.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        await asyncio.sleep(0)
        config.relogio.tick(30)
