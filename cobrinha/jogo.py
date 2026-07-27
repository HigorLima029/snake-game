"""Orquestração do jogo: entrada de teclado, laço principal e ponto de entrada."""
from __future__ import annotations

import asyncio
import sys
from typing import Dict, List, Optional

import pygame

from . import config, sons, telas
from .entidades import (
    Cobra,
    criar_cobra,
    criar_particulas,
    calcular_fase,
    escolher_direcao_bot,
    gerar_comida,
    gerar_obstaculos,
    obstaculos_extra_da_fase,
    Particula,
)


def aplicar_tecla_direcao(tecla: int, modo: str, cobras: List[Cobra]) -> None:
    """Atualiza a próxima direção do(s) jogador(es) humano(s) com base na tecla pressionada."""
    jogador1 = cobras[0]
    jogador2: Optional[Cobra] = cobras[1] if len(cobras) > 1 else None
    bloco = config.TAMANHO_BLOCO

    if modo == "2 Jogadores":
        if tecla == pygame.K_w and jogador1.direcao != (0, bloco):
            jogador1.proxima_direcao = (0, -bloco)
        elif tecla == pygame.K_s and jogador1.direcao != (0, -bloco):
            jogador1.proxima_direcao = (0, bloco)
        elif tecla == pygame.K_a and jogador1.direcao != (bloco, 0):
            jogador1.proxima_direcao = (-bloco, 0)
        elif tecla == pygame.K_d and jogador1.direcao != (-bloco, 0):
            jogador1.proxima_direcao = (bloco, 0)
        elif jogador2 is not None:
            if tecla == pygame.K_UP and jogador2.direcao != (0, bloco):
                jogador2.proxima_direcao = (0, -bloco)
            elif tecla == pygame.K_DOWN and jogador2.direcao != (0, -bloco):
                jogador2.proxima_direcao = (0, bloco)
            elif tecla == pygame.K_LEFT and jogador2.direcao != (bloco, 0):
                jogador2.proxima_direcao = (-bloco, 0)
            elif tecla == pygame.K_RIGHT and jogador2.direcao != (-bloco, 0):
                jogador2.proxima_direcao = (bloco, 0)
    else:
        if tecla in (pygame.K_UP, pygame.K_w) and jogador1.direcao != (0, bloco):
            jogador1.proxima_direcao = (0, -bloco)
        elif tecla in (pygame.K_DOWN, pygame.K_s) and jogador1.direcao != (0, -bloco):
            jogador1.proxima_direcao = (0, bloco)
        elif tecla in (pygame.K_LEFT, pygame.K_a) and jogador1.direcao != (bloco, 0):
            jogador1.proxima_direcao = (-bloco, 0)
        elif tecla in (pygame.K_RIGHT, pygame.K_d) and jogador1.direcao != (-bloco, 0):
            jogador1.proxima_direcao = (bloco, 0)


async def rodar_jogo(indice_tema: int, recorde: int) -> List[Cobra]:
    tema = config.TEMAS[indice_tema]
    dificuldade = config.DIFICULDADES[config.CONFIG["dificuldade"]]
    velocidade_base = min(
        max(
            config.CONFIG["velocidade_inicial"] + dificuldade["modificador_velocidade"],
            config.VELOCIDADE_INICIAL_MIN,
        ),
        config.VELOCIDADE_MAXIMA,
    )
    modo = config.CONFIG["modo_jogo"]

    if modo == "2 Jogadores":
        cobras = [
            criar_cobra((100, 200), (config.TAMANHO_BLOCO, 0), "jogador1"),
            criar_cobra((480, 200), (-config.TAMANHO_BLOCO, 0), "jogador2"),
        ]
    elif modo == "Jogador vs Bot":
        cobras = [
            criar_cobra((100, 200), (config.TAMANHO_BLOCO, 0), "jogador1"),
            criar_cobra((480, 200), (-config.TAMANHO_BLOCO, 0), "bot"),
        ]
    else:
        cobras = [criar_cobra((config.LARGURA // 2, config.ALTURA // 2), (config.TAMANHO_BLOCO, 0), "jogador1")]

    ocupados_iniciais: List[config.Posicao] = []
    for cobra in cobras:
        ocupados_iniciais += cobra.corpo

    if config.CONFIG["mapa_personalizado"]:
        mapa = config.carregar_mapa_personalizado()
        obstaculos = [celula for celula in mapa if celula not in ocupados_iniciais]
    else:
        obstaculos = gerar_obstaculos(dificuldade["obstaculos"], ocupados_iniciais)

    comida, comida_especial = gerar_comida(ocupados_iniciais + obstaculos)

    pausado = False
    particulas: List[Particula] = []
    tempo_acumulado = 0.0
    fase_atual = 1
    aviso_fase_ate = 0

    while True:
        dt = config.relogio.tick(config.FPS_RENDER) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_ESCAPE, pygame.K_p):
                    pausado = not pausado
                elif not pausado:
                    aplicar_tecla_direcao(evento.key, modo, cobras)

        if pausado:
            telas.tela_de_pausa()
            await asyncio.sleep(0)
            continue

        tempo_acumulado += dt

        while any(c.viva for c in cobras):
            pontuacao_max = max(c.pontuacao for c in cobras)
            velocidade_atual = min(velocidade_base + pontuacao_max // config.PONTOS_POR_NIVEL, config.VELOCIDADE_MAXIMA)
            intervalo = 1.0 / velocidade_atual
            if tempo_acumulado < intervalo:
                break
            tempo_acumulado -= intervalo

            for cobra in cobras:
                if cobra.viva:
                    cobra.corpo_anterior = list(cobra.corpo)

            for cobra in cobras:
                if not cobra.viva:
                    continue
                if cobra.controlador == "bot":
                    perigos = set(obstaculos)
                    for outra in cobras:
                        perigos.update(outra.corpo)
                    cobra.proxima_direcao = escolher_direcao_bot(cobra.corpo[0], cobra.direcao, comida, perigos)
                cobra.direcao = cobra.proxima_direcao

            novas_cabecas: Dict[int, config.Posicao] = {}
            for cobra in cobras:
                if not cobra.viva:
                    continue
                cabeca = cobra.corpo[0]
                d = cobra.direcao
                nova = (cabeca[0] + d[0], cabeca[1] + d[1])
                if config.CONFIG["parede_atravessavel"]:
                    nova = (nova[0] % config.LARGURA, nova[1] % config.ALTURA)
                novas_cabecas[id(cobra)] = nova

            agora = pygame.time.get_ticks()
            for cobra in cobras:
                if not cobra.viva:
                    continue
                nova = novas_cabecas[id(cobra)]
                protegido = agora < cobra.escudo_ate
                morreu = False
                if not config.CONFIG["parede_atravessavel"] and (
                    nova[0] < 0 or nova[0] >= config.LARGURA or nova[1] < 0 or nova[1] >= config.ALTURA
                ):
                    morreu = True
                elif not protegido and nova in obstaculos:
                    morreu = True
                elif not protegido and nova in cobra.corpo:
                    morreu = True
                else:
                    for outra in cobras:
                        if outra is cobra or not outra.viva:
                            continue
                        if not protegido and nova in outra.corpo:
                            morreu = True
                        if nova == novas_cabecas.get(id(outra)):
                            morreu = True
                if morreu:
                    cobra.viva = False
                    sons.SOM_COLIDIR.play()

            comida_comida = False
            for cobra in cobras:
                if not cobra.viva:
                    continue
                nova = novas_cabecas[id(cobra)]
                cobra.corpo.insert(0, nova)
                if nova == comida:
                    comida_comida = True
                    if comida_especial:
                        cobra.pontuacao += 5
                        cobra.escudo_ate = agora + config.DURACAO_ESCUDO_MS
                        particulas += criar_particulas(*comida, config.DOURADO, 20)
                    else:
                        cobra.pontuacao += 1
                        particulas += criar_particulas(*comida, tema["comida"], 12)
                    sons.SOM_COMER.play()
                else:
                    cobra.corpo.pop()

            if comida_comida:
                ocupados = list(obstaculos)
                for cobra in cobras:
                    ocupados += cobra.corpo
                comida, comida_especial = gerar_comida(ocupados)

            pontuacao_max = max(c.pontuacao for c in cobras)
            nova_fase = calcular_fase(pontuacao_max)
            if nova_fase > fase_atual:
                qtd_novos = obstaculos_extra_da_fase(nova_fase) - obstaculos_extra_da_fase(fase_atual)
                if qtd_novos > 0:
                    ocupados = list(obstaculos) + [comida]
                    for cobra in cobras:
                        ocupados += cobra.corpo
                    obstaculos += gerar_obstaculos(qtd_novos, ocupados)
                fase_atual = nova_fase
                aviso_fase_ate = pygame.time.get_ticks() + 1500
                sons.SOM_SELECIONAR.play()

        if not any(c.viva for c in cobras):
            return cobras

        for particula in particulas:
            particula.atualizar(dt)
        particulas = [p for p in particulas if p.viva()]

        pontuacao_max = max(c.pontuacao for c in cobras)
        velocidade_atual = min(velocidade_base + pontuacao_max // config.PONTOS_POR_NIVEL, config.VELOCIDADE_MAXIMA)
        intervalo = 1.0 / velocidade_atual
        progresso = min(tempo_acumulado / intervalo, 1.0) if intervalo > 0 else 1.0

        telas.desenhar_jogo(
            tema, cobras, progresso, comida, comida_especial, obstaculos,
            recorde, velocidade_atual, fase_atual, aviso_fase_ate, particulas,
        )

        await asyncio.sleep(0)


async def main() -> None:
    recorde = config.carregar_recorde()
    config.carregar_config()
    sons.aplicar_volume(config.CONFIG["volume"])
    ranking = config.carregar_ranking()
    indice_tema = 0

    while True:
        indice_tema = await telas.menu_principal(indice_tema, recorde)

        continuar = True
        while continuar:
            cobras = await rodar_jogo(indice_tema, recorde)
            modo = config.CONFIG["modo_jogo"]

            if modo != "2 Jogadores":
                pontuacao = cobras[0].pontuacao
                if pontuacao > recorde:
                    recorde = pontuacao
                    config.salvar_recorde(recorde)
                if pontuacao > 0 and config.entra_no_ranking(ranking, pontuacao):
                    nome = await telas.tela_entrada_nome(pontuacao)
                    ranking = config.adicionar_ao_ranking(ranking, nome, pontuacao)
                    config.salvar_ranking(ranking)

            escolha = await telas.tela_de_fim(cobras, modo, recorde)
            if escolha == "menu":
                continuar = False
            elif escolha == "jogar":
                continue
