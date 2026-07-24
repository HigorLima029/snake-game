import asyncio
import json
import math
import os
import random
import sys

import numpy as np
import pygame

pygame.init()
pygame.mixer.init()

# ---------- Configurações básicas ----------
LARGURA, ALTURA = 600, 400
TAMANHO_BLOCO = 20
VELOCIDADE_MAXIMA = 20
PONTOS_POR_NIVEL = 3  # a cada X pontos, a velocidade aumenta 1
VELOCIDADE_INICIAL_MIN = 4
VELOCIDADE_INICIAL_MAX = 15
FPS_RENDER = 60  # taxa de desenho (independente da velocidade lógica do jogo)
DURACAO_ESCUDO_MS = 3000  # tempo de efeito da comida especial
CHANCE_COMIDA_ESPECIAL = 0.2  # 20% de chance da comida nascer especial (dourada)
PONTOS_POR_FASE = 8
OBSTACULOS_POR_FASE = 2
OBSTACULOS_MAXIMOS_FASE = 12

# Cores gerais (usadas fora dos temas)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (40, 40, 40)
AMARELO = (230, 200, 40)
DOURADO = (255, 215, 0)
COR_CABECA_2 = (230, 60, 210)
COR_CORPO_2 = (150, 50, 150)

CAMINHO_BASE = os.path.dirname(os.path.abspath(__file__))
CAMINHO_RECORDE = os.path.join(CAMINHO_BASE, "recorde.txt")
CAMINHO_CONFIG = os.path.join(CAMINHO_BASE, "config.txt")
CAMINHO_MAPA = os.path.join(CAMINHO_BASE, "mapa_personalizado.txt")
CAMINHO_RANKING = os.path.join(CAMINHO_BASE, "ranking.json")

MODOS_JOGO = ["1 Jogador", "2 Jogadores", "Jogador vs Bot"]

# Configurações ajustáveis pelo jogador
CONFIG = {
    "volume": 0.7,
    "velocidade_inicial": 8,
    "parede_atravessavel": False,
    "dificuldade": "Médio",
    "modo_jogo": "1 Jogador",
    "mapa_personalizado": False,
}

# Cada dificuldade define quantos obstáculos existem no mapa e um ajuste na velocidade base
DIFICULDADES = {
    "Fácil": {"obstaculos": 0, "modificador_velocidade": -2},
    "Médio": {"obstaculos": 5, "modificador_velocidade": 0},
    "Difícil": {"obstaculos": 10, "modificador_velocidade": 3},
}
LISTA_DIFICULDADES = ["Fácil", "Médio", "Difícil"]

DIRECOES = [(0, -TAMANHO_BLOCO), (0, TAMANHO_BLOCO), (-TAMANHO_BLOCO, 0), (TAMANHO_BLOCO, 0)]

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo da Cobrinha")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 20)
fonte_grande = pygame.font.SysFont("arial", 44)

# ---------- Temas ----------
TEMAS = [
    {
        "nome": "Clássico",
        "fundo": PRETO,
        "grade": CINZA,
        "cabeca": (0, 120, 0),
        "corpo": (0, 200, 0),
        "comida": (200, 0, 0),
    },
    {
        "nome": "Neon",
        "fundo": (10, 10, 25),
        "grade": (30, 30, 55),
        "cabeca": (255, 0, 200),
        "corpo": (0, 220, 255),
        "comida": (255, 230, 0),
    },
    {
        "nome": "Gelo",
        "fundo": (15, 30, 45),
        "grade": (35, 55, 70),
        "cabeca": (200, 240, 255),
        "corpo": (100, 190, 230),
        "comida": (255, 120, 120),
    },
    {
        "nome": "Deserto",
        "fundo": (40, 30, 15),
        "grade": (70, 55, 30),
        "cabeca": (150, 90, 20),
        "corpo": (220, 170, 60),
        "comida": (80, 160, 60),
    },
]


# ---------- Sons (gerados na hora, sem precisar de arquivos externos) ----------
def gerar_tom(frequencia, duracao=0.12, volume=0.3, taxa=44100):
    n_amostras = int(taxa * duracao)
    t = np.linspace(0, duracao, n_amostras, False)
    onda = np.sin(frequencia * t * 2 * np.pi)
    envelope = np.linspace(1, 0, n_amostras)  # evita "clique" no final do som
    onda = (onda * envelope * volume * 32767).astype(np.int16)
    estereo = np.column_stack((onda, onda))
    return pygame.sndarray.make_sound(np.ascontiguousarray(estereo))


SOM_COMER = gerar_tom(880, duracao=0.09, volume=0.35)
SOM_COLIDIR = gerar_tom(140, duracao=0.35, volume=0.4)
SOM_SELECIONAR = gerar_tom(600, duracao=0.06, volume=0.25)


# ---------- Recorde ----------
def carregar_recorde():
    if os.path.exists(CAMINHO_RECORDE):
        try:
            with open(CAMINHO_RECORDE, "r") as arquivo:
                return int(arquivo.read().strip())
        except (ValueError, OSError):
            return 0
    return 0


def salvar_recorde(pontuacao):
    with open(CAMINHO_RECORDE, "w") as arquivo:
        arquivo.write(str(pontuacao))


# ---------- Configurações (volume, velocidade, parede, dificuldade, modo, mapa) ----------
def carregar_config():
    if os.path.exists(CAMINHO_CONFIG):
        try:
            with open(CAMINHO_CONFIG, "r") as arquivo:
                linhas = arquivo.read().strip().splitlines()
                CONFIG["volume"] = min(max(float(linhas[0]), 0.0), 1.0)
                CONFIG["velocidade_inicial"] = min(
                    max(int(linhas[1]), VELOCIDADE_INICIAL_MIN), VELOCIDADE_INICIAL_MAX
                )
                if len(linhas) > 2:
                    CONFIG["parede_atravessavel"] = linhas[2].strip() == "1"
                if len(linhas) > 3 and linhas[3].strip() in DIFICULDADES:
                    CONFIG["dificuldade"] = linhas[3].strip()
                if len(linhas) > 4 and linhas[4].strip() in MODOS_JOGO:
                    CONFIG["modo_jogo"] = linhas[4].strip()
                if len(linhas) > 5:
                    CONFIG["mapa_personalizado"] = linhas[5].strip() == "1"
        except (ValueError, OSError, IndexError):
            pass
    aplicar_volume()


def salvar_config():
    with open(CAMINHO_CONFIG, "w") as arquivo:
        arquivo.write(
            f"{CONFIG['volume']}\n{CONFIG['velocidade_inicial']}\n"
            f"{1 if CONFIG['parede_atravessavel'] else 0}\n{CONFIG['dificuldade']}\n"
            f"{CONFIG['modo_jogo']}\n{1 if CONFIG['mapa_personalizado'] else 0}"
        )


def aplicar_volume():
    for som in (SOM_COMER, SOM_COLIDIR, SOM_SELECIONAR):
        som.set_volume(CONFIG["volume"])


# ---------- Ranking local ----------
def carregar_ranking():
    if os.path.exists(CAMINHO_RANKING):
        try:
            with open(CAMINHO_RANKING, "r") as arquivo:
                dados = json.load(arquivo)
                if isinstance(dados, list):
                    return dados
        except (ValueError, OSError):
            pass
    return []


def salvar_ranking(ranking):
    with open(CAMINHO_RANKING, "w") as arquivo:
        json.dump(ranking, arquivo)


def entra_no_ranking(ranking, pontuacao):
    if len(ranking) < 10:
        return True
    return pontuacao > min(registro["pontuacao"] for registro in ranking)


def adicionar_ao_ranking(ranking, nome, pontuacao):
    novo_ranking = ranking + [{"nome": nome, "pontuacao": pontuacao}]
    novo_ranking.sort(key=lambda registro: registro["pontuacao"], reverse=True)
    return novo_ranking[:10]


# ---------- Mapa personalizado ----------
def carregar_mapa_personalizado():
    celulas = []
    if os.path.exists(CAMINHO_MAPA):
        try:
            with open(CAMINHO_MAPA, "r") as arquivo:
                for linha in arquivo:
                    linha = linha.strip()
                    if not linha:
                        continue
                    x_str, y_str = linha.split(",")
                    celulas.append((int(x_str), int(y_str)))
        except (ValueError, OSError):
            return []
    return celulas


def salvar_mapa_personalizado(celulas):
    with open(CAMINHO_MAPA, "w") as arquivo:
        for x, y in celulas:
            arquivo.write(f"{x},{y}\n")


def desenhar_texto(texto, fonte_usada, cor, x, y, centralizado=False):
    superficie = fonte_usada.render(texto, True, cor)
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)
    return rect


def gerar_posicao_livre(ocupados):
    while True:
        pos = (
            random.randrange(0, LARGURA, TAMANHO_BLOCO),
            random.randrange(0, ALTURA, TAMANHO_BLOCO),
        )
        if pos not in ocupados:
            return pos


def gerar_obstaculos(quantidade, ocupados):
    obstaculos = []
    ocupados_atual = list(ocupados)
    for _ in range(quantidade):
        pos = gerar_posicao_livre(ocupados_atual)
        obstaculos.append(pos)
        ocupados_atual.append(pos)
    return obstaculos


def gerar_comida(ocupados):
    pos = gerar_posicao_livre(ocupados)
    especial = random.random() < CHANCE_COMIDA_ESPECIAL
    return pos, especial


# ---------- Partículas (efeito visual ao comer) ----------
class Particula:
    def __init__(self, x, y, cor):
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

    def atualizar(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt

    def viva(self):
        return self.vida > 0

    def desenhar(self, superficie):
        fracao = max(0.0, self.vida / self.vida_total)
        raio = max(1, int(self.raio_base * fracao))
        pygame.draw.circle(superficie, self.cor, (int(self.x), int(self.y)), raio)


def criar_particulas(x, y, cor, quantidade=14):
    centro_x = x + TAMANHO_BLOCO // 2
    centro_y = y + TAMANHO_BLOCO // 2
    return [Particula(centro_x, centro_y, cor) for _ in range(quantidade)]


# ---------- IA do bot ----------
def oposto(direcao):
    return (-direcao[0], -direcao[1])


def escolher_direcao_bot(cabeca, direcao_atual, comida, celulas_perigosas):
    candidatas = [d for d in DIRECOES if d != oposto(direcao_atual)]
    seguras = []
    for direcao in candidatas:
        proximo = (cabeca[0] + direcao[0], cabeca[1] + direcao[1])
        if CONFIG["parede_atravessavel"]:
            proximo = (proximo[0] % LARGURA, proximo[1] % ALTURA)
        elif proximo[0] < 0 or proximo[0] >= LARGURA or proximo[1] < 0 or proximo[1] >= ALTURA:
            continue
        if proximo in celulas_perigosas:
            continue
        seguras.append((direcao, proximo))

    if not seguras:
        return candidatas[0] if candidatas else direcao_atual

    def distancia(pos):
        return abs(pos[0] - comida[0]) + abs(pos[1] - comida[1])

    seguras.sort(key=lambda item: distancia(item[1]))
    return seguras[0][0]


# ---------- Fases ----------
def calcular_fase(pontuacao):
    return 1 + pontuacao // PONTOS_POR_FASE


def obstaculos_extra_da_fase(fase):
    return min((fase - 1) * OBSTACULOS_POR_FASE, OBSTACULOS_MAXIMOS_FASE)


def criar_cobra(posicao_inicial, direcao_inicial, controlador):
    return {
        "corpo": [posicao_inicial],
        "corpo_anterior": [posicao_inicial],
        "direcao": direcao_inicial,
        "proxima_direcao": direcao_inicial,
        "pontuacao": 0,
        "escudo_ate": 0,
        "viva": True,
        "controlador": controlador,  # "jogador1", "jogador2" ou "bot"
    }


def interpolar_posicao(origem, destino, progresso):
    # Evita um "arrastão" visual quando a cobra atravessa de um lado ao outro da tela
    dx = destino[0] - origem[0]
    dy = destino[1] - origem[1]
    if abs(dx) > TAMANHO_BLOCO * 1.5 or abs(dy) > TAMANHO_BLOCO * 1.5:
        return destino
    return (origem[0] + dx * progresso, origem[1] + dy * progresso)


def desenhar_jogo(
    tema, cobras, progresso, comida, comida_especial, obstaculos,
    recorde, velocidade_atual, fase_atual, aviso_fase_ate, particulas,
):
    tela.fill(tema["fundo"])

    for x in range(0, LARGURA, TAMANHO_BLOCO):
        pygame.draw.line(tela, tema["grade"], (x, 0), (x, ALTURA))
    for y in range(0, ALTURA, TAMANHO_BLOCO):
        pygame.draw.line(tela, tema["grade"], (0, y), (LARGURA, y))

    for obstaculo in obstaculos:
        pygame.draw.rect(tela, (95, 95, 95), (*obstaculo, TAMANHO_BLOCO, TAMANHO_BLOCO))
        pygame.draw.rect(tela, (60, 60, 60), (*obstaculo, TAMANHO_BLOCO, TAMANHO_BLOCO), 2)

    if comida_especial:
        pulso = int(3 * math.sin(pygame.time.get_ticks() / 120))
        centro = (comida[0] + TAMANHO_BLOCO // 2, comida[1] + TAMANHO_BLOCO // 2)
        pygame.draw.circle(tela, DOURADO, centro, TAMANHO_BLOCO // 2 + 3 + pulso)
        pygame.draw.circle(tela, (255, 255, 200), centro, TAMANHO_BLOCO // 3)
    else:
        pygame.draw.rect(tela, tema["comida"], (*comida, TAMANHO_BLOCO, TAMANHO_BLOCO))

    for particula in particulas:
        particula.desenhar(tela)

    agora = pygame.time.get_ticks()
    for indice_cobra, cobra in enumerate(cobras):
        cor_cabeca, cor_corpo = (tema["cabeca"], tema["corpo"]) if indice_cobra == 0 else (COR_CABECA_2, COR_CORPO_2)
        protegido = agora < cobra["escudo_ate"]
        for i, segmento_novo in enumerate(cobra["corpo"]):
            origem = cobra["corpo_anterior"][i] if i < len(cobra["corpo_anterior"]) else segmento_novo
            x, y = interpolar_posicao(origem, segmento_novo, progresso)
            cor = cor_cabeca if i == 0 else cor_corpo
            if not cobra["viva"]:
                cor = (80, 80, 80)
            pygame.draw.rect(tela, cor, (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO))
            if protegido:
                pygame.draw.rect(tela, DOURADO, (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO), 2)

    pontuacao_max = max(c["pontuacao"] for c in cobras)

    if len(cobras) > 1:
        rotulo2 = "Bot" if cobras[1]["controlador"] == "bot" else "Jogador 2"
        desenhar_texto(f"Jogador 1: {cobras[0]['pontuacao']}", fonte, BRANCO, 10, 10)
        desenhar_texto(f"{rotulo2}: {cobras[1]['pontuacao']}", fonte, (230, 140, 230), 10, 33)
    else:
        desenhar_texto(f"Pontuação: {cobras[0]['pontuacao']}", fonte, BRANCO, 10, 10)
        desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, 10, 33)

    desenhar_texto(f"Fase: {fase_atual}", fonte, (170, 170, 170), LARGURA - 80, 33)
    desenhar_texto("P/ESC: pausar", fonte, (150, 150, 150), LARGURA - 140, 10)

    if velocidade_atual >= VELOCIDADE_MAXIMA:
        desenhar_texto("Velocidade máxima!", fonte, AMARELO, 10, 58)
    else:
        pontos_restantes = PONTOS_POR_NIVEL - (pontuacao_max % PONTOS_POR_NIVEL)
        desenhar_texto(f"Próx. velocidade em {pontos_restantes} ponto(s)", fonte, (150, 150, 150), 10, 58)
        progresso_barra = 1 - (pontos_restantes / PONTOS_POR_NIVEL)
        largura_barra = 150
        pygame.draw.rect(tela, (60, 60, 60), (10, 82, largura_barra, 8))
        pygame.draw.rect(tela, AMARELO, (10, 82, int(largura_barra * progresso_barra), 8))

    if agora < aviso_fase_ate:
        desenhar_texto(f"Fase {fase_atual}!", fonte_grande, AMARELO, LARGURA // 2, ALTURA // 2 - 80, centralizado=True)

    pygame.display.update()


# ---------- Menu principal ----------
async def menu_principal(indice_tema, recorde):
    opcoes = ["Jogar", "Tema", "Configurações", "Editor de Mapa", "Ranking", "Sair"]
    selecionado = 0

    while True:
        tema = TEMAS[indice_tema]
        tela.fill(PRETO)
        desenhar_texto("JOGO DA COBRINHA", fonte_grande, AMARELO, LARGURA // 2, 42, centralizado=True)
        desenhar_texto(
            f"Recorde: {recorde}   |   Dificuldade: {CONFIG['dificuldade']}   |   Modo: {CONFIG['modo_jogo']}",
            fonte, (170, 170, 170), LARGURA // 2, 78, centralizado=True,
        )

        for i, opcao in enumerate(opcoes):
            cor = AMARELO if i == selecionado else BRANCO
            texto = opcao
            if opcao == "Tema":
                texto = f"< Tema: {tema['nome']} >"
            desenhar_texto(texto, fonte, cor, LARGURA // 2, 118 + i * 36, centralizado=True)

        desenhar_texto(
            "seta cima/baixo: navegar   esquerda/direita: trocar tema   Enter: confirmar",
            fonte,
            (150, 150, 150),
            LARGURA // 2,
            ALTURA - 15,
            centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    selecionado = (selecionado - 1) % len(opcoes)
                    SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    selecionado = (selecionado + 1) % len(opcoes)
                    SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_LEFT, pygame.K_a) and opcoes[selecionado] == "Tema":
                    indice_tema = (indice_tema - 1) % len(TEMAS)
                    SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_RIGHT, pygame.K_d) and opcoes[selecionado] == "Tema":
                    indice_tema = (indice_tema + 1) % len(TEMAS)
                    SOM_SELECIONAR.play()
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
        relogio.tick(30)


async def tela_configuracoes():
    opcoes = ["Volume", "Velocidade inicial", "Parede", "Dificuldade", "Modo", "Mapa", "Voltar"]
    selecionado = 0

    while True:
        tela.fill(PRETO)
        desenhar_texto("CONFIGURAÇÕES", fonte_grande, AMARELO, LARGURA // 2, 35, centralizado=True)

        for i, opcao in enumerate(opcoes):
            cor = AMARELO if i == selecionado else BRANCO
            if opcao == "Volume":
                texto = f"< Volume: {int(CONFIG['volume'] * 100)}% >"
            elif opcao == "Velocidade inicial":
                texto = f"< Velocidade inicial: {CONFIG['velocidade_inicial']} >"
            elif opcao == "Parede":
                estado = "Atravessável" if CONFIG["parede_atravessavel"] else "Sólida"
                texto = f"< Parede: {estado} >"
            elif opcao == "Dificuldade":
                texto = f"< Dificuldade: {CONFIG['dificuldade']} >"
            elif opcao == "Modo":
                texto = f"< Modo: {CONFIG['modo_jogo']} >"
            elif opcao == "Mapa":
                estado = "Personalizado" if CONFIG["mapa_personalizado"] else "Aleatório"
                texto = f"< Mapa: {estado} >"
            else:
                texto = opcao
            desenhar_texto(texto, fonte, cor, LARGURA // 2, 78 + i * 33, centralizado=True)

        desenhar_texto(
            "esquerda/direita: ajustar   Enter/ESC: voltar",
            fonte,
            (150, 150, 150),
            LARGURA // 2,
            ALTURA - 15,
            centralizado=True,
        )
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    selecionado = (selecionado - 1) % len(opcoes)
                    SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    selecionado = (selecionado + 1) % len(opcoes)
                    SOM_SELECIONAR.play()
                elif evento.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    direita = evento.key in (pygame.K_RIGHT, pygame.K_d)
                    opcao = opcoes[selecionado]
                    alterou = True
                    if opcao == "Volume":
                        delta = 0.1 if direita else -0.1
                        CONFIG["volume"] = round(min(max(CONFIG["volume"] + delta, 0.0), 1.0), 2)
                        aplicar_volume()
                    elif opcao == "Velocidade inicial":
                        delta = 1 if direita else -1
                        CONFIG["velocidade_inicial"] = min(
                            max(CONFIG["velocidade_inicial"] + delta, VELOCIDADE_INICIAL_MIN),
                            VELOCIDADE_INICIAL_MAX,
                        )
                    elif opcao == "Parede":
                        CONFIG["parede_atravessavel"] = not CONFIG["parede_atravessavel"]
                    elif opcao == "Dificuldade":
                        idx = LISTA_DIFICULDADES.index(CONFIG["dificuldade"])
                        idx = (idx + (1 if direita else -1)) % len(LISTA_DIFICULDADES)
                        CONFIG["dificuldade"] = LISTA_DIFICULDADES[idx]
                    elif opcao == "Modo":
                        idx = MODOS_JOGO.index(CONFIG["modo_jogo"])
                        idx = (idx + (1 if direita else -1)) % len(MODOS_JOGO)
                        CONFIG["modo_jogo"] = MODOS_JOGO[idx]
                    elif opcao == "Mapa":
                        CONFIG["mapa_personalizado"] = not CONFIG["mapa_personalizado"]
                    else:
                        alterou = False
                    if alterou:
                        SOM_SELECIONAR.play()
                        salvar_config()
                elif evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    if opcoes[selecionado] == "Voltar" or evento.key == pygame.K_ESCAPE:
                        return

        await asyncio.sleep(0)
        relogio.tick(30)


async def tela_editor_mapa():
    colunas = LARGURA // TAMANHO_BLOCO
    linhas = ALTURA // TAMANHO_BLOCO
    obstaculos = set(carregar_mapa_personalizado())
    cursor_x, cursor_y = colunas // 2, linhas // 2

    while True:
        tela.fill(PRETO)
        for x in range(0, LARGURA, TAMANHO_BLOCO):
            pygame.draw.line(tela, CINZA, (x, 0), (x, ALTURA))
        for y in range(0, ALTURA, TAMANHO_BLOCO):
            pygame.draw.line(tela, CINZA, (0, y), (LARGURA, y))

        for (ox, oy) in obstaculos:
            pygame.draw.rect(tela, (95, 95, 95), (ox, oy, TAMANHO_BLOCO, TAMANHO_BLOCO))

        cursor_pos = (cursor_x * TAMANHO_BLOCO, cursor_y * TAMANHO_BLOCO)
        pygame.draw.rect(tela, AMARELO, (*cursor_pos, TAMANHO_BLOCO, TAMANHO_BLOCO), 3)

        desenhar_texto("EDITOR DE MAPA", fonte, AMARELO, LARGURA // 2, 16, centralizado=True)
        desenhar_texto(
            "setas: mover   espaço/enter: alternar obstáculo   C: limpar   S: salvar   ESC: cancelar",
            fonte, (150, 150, 150), LARGURA // 2, ALTURA - 12, centralizado=True,
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
                    pos = (cursor_x * TAMANHO_BLOCO, cursor_y * TAMANHO_BLOCO)
                    if pos in obstaculos:
                        obstaculos.discard(pos)
                    else:
                        obstaculos.add(pos)
                    SOM_SELECIONAR.play()
                elif evento.key == pygame.K_c:
                    obstaculos.clear()
                elif evento.key == pygame.K_s:
                    salvar_mapa_personalizado(sorted(obstaculos))
                    return
                elif evento.key == pygame.K_ESCAPE:
                    return

        await asyncio.sleep(0)
        relogio.tick(30)


async def tela_ranking():
    ranking = carregar_ranking()
    while True:
        tela.fill(PRETO)
        desenhar_texto("RANKING LOCAL", fonte_grande, AMARELO, LARGURA // 2, 36, centralizado=True)
        if not ranking:
            desenhar_texto("Ainda não há pontuações registradas.", fonte, BRANCO, LARGURA // 2, 110, centralizado=True)
        else:
            for i, registro in enumerate(ranking[:10]):
                texto = f"{i + 1}. {registro['nome']} — {registro['pontuacao']} pts"
                desenhar_texto(texto, fonte, BRANCO, LARGURA // 2, 85 + i * 27, centralizado=True)
        desenhar_texto("Enter ou ESC: voltar", fonte, (150, 150, 150), LARGURA // 2, ALTURA - 15, centralizado=True)
        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                return

        await asyncio.sleep(0)
        relogio.tick(30)


async def tela_entrada_nome(pontuacao):
    nome = ""
    while True:
        tela.fill(PRETO)
        desenhar_texto("Novo recorde no ranking!", fonte_grande, AMARELO, LARGURA // 2, 90, centralizado=True)
        desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, LARGURA // 2, 140, centralizado=True)
        desenhar_texto("Digite seu nome:", fonte, BRANCO, LARGURA // 2, 180, centralizado=True)
        desenhar_texto(nome + "_", fonte_grande, AMARELO, LARGURA // 2, 220, centralizado=True)
        desenhar_texto("Enter: confirmar   Backspace: apagar", fonte, (150, 150, 150), LARGURA // 2, ALTURA - 15, centralizado=True)
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
        relogio.tick(30)


def tela_de_pausa():
    overlay = pygame.Surface((LARGURA, ALTURA))
    overlay.set_alpha(180)
    overlay.fill(PRETO)
    tela.blit(overlay, (0, 0))
    desenhar_texto("PAUSADO", fonte_grande, AMARELO, LARGURA // 2, ALTURA // 2 - 20, centralizado=True)
    desenhar_texto("Pressione P ou ESC para continuar", fonte, BRANCO, LARGURA // 2, ALTURA // 2 + 30, centralizado=True)
    pygame.display.update()


async def tela_de_fim(cobras, modo_jogo, recorde):
    tela.fill(PRETO)
    desenhar_texto("Fim de jogo!", fonte_grande, (200, 40, 40), LARGURA // 2, 65, centralizado=True)

    if modo_jogo == "2 Jogadores":
        p1, p2 = cobras[0]["pontuacao"], cobras[1]["pontuacao"]
        desenhar_texto(f"Jogador 1: {p1} pontos", fonte, BRANCO, LARGURA // 2, 130, centralizado=True)
        desenhar_texto(f"Jogador 2: {p2} pontos", fonte, BRANCO, LARGURA // 2, 158, centralizado=True)
        if p1 > p2:
            resultado = "Jogador 1 venceu!"
        elif p2 > p1:
            resultado = "Jogador 2 venceu!"
        else:
            resultado = "Empate!"
        desenhar_texto(resultado, fonte, AMARELO, LARGURA // 2, 195, centralizado=True)
    else:
        pontuacao = cobras[0]["pontuacao"]
        desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, LARGURA // 2, 130, centralizado=True)
        if pontuacao > recorde:
            desenhar_texto("Novo recorde!", fonte, AMARELO, LARGURA // 2, 160, centralizado=True)
        else:
            desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, LARGURA // 2, 160, centralizado=True)

    desenhar_texto(
        "R: jogar de novo    M: menu    Q: sair", fonte, (180, 180, 180), LARGURA // 2, ALTURA - 40, centralizado=True
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
        relogio.tick(30)


def aplicar_tecla_direcao(tecla, modo, cobras):
    jogador1 = cobras[0]
    jogador2 = cobras[1] if len(cobras) > 1 else None

    if modo == "2 Jogadores":
        if tecla == pygame.K_w and jogador1["direcao"] != (0, TAMANHO_BLOCO):
            jogador1["proxima_direcao"] = (0, -TAMANHO_BLOCO)
        elif tecla == pygame.K_s and jogador1["direcao"] != (0, -TAMANHO_BLOCO):
            jogador1["proxima_direcao"] = (0, TAMANHO_BLOCO)
        elif tecla == pygame.K_a and jogador1["direcao"] != (TAMANHO_BLOCO, 0):
            jogador1["proxima_direcao"] = (-TAMANHO_BLOCO, 0)
        elif tecla == pygame.K_d and jogador1["direcao"] != (-TAMANHO_BLOCO, 0):
            jogador1["proxima_direcao"] = (TAMANHO_BLOCO, 0)
        elif jogador2 is not None:
            if tecla == pygame.K_UP and jogador2["direcao"] != (0, TAMANHO_BLOCO):
                jogador2["proxima_direcao"] = (0, -TAMANHO_BLOCO)
            elif tecla == pygame.K_DOWN and jogador2["direcao"] != (0, -TAMANHO_BLOCO):
                jogador2["proxima_direcao"] = (0, TAMANHO_BLOCO)
            elif tecla == pygame.K_LEFT and jogador2["direcao"] != (TAMANHO_BLOCO, 0):
                jogador2["proxima_direcao"] = (-TAMANHO_BLOCO, 0)
            elif tecla == pygame.K_RIGHT and jogador2["direcao"] != (-TAMANHO_BLOCO, 0):
                jogador2["proxima_direcao"] = (TAMANHO_BLOCO, 0)
    else:
        if tecla in (pygame.K_UP, pygame.K_w) and jogador1["direcao"] != (0, TAMANHO_BLOCO):
            jogador1["proxima_direcao"] = (0, -TAMANHO_BLOCO)
        elif tecla in (pygame.K_DOWN, pygame.K_s) and jogador1["direcao"] != (0, -TAMANHO_BLOCO):
            jogador1["proxima_direcao"] = (0, TAMANHO_BLOCO)
        elif tecla in (pygame.K_LEFT, pygame.K_a) and jogador1["direcao"] != (TAMANHO_BLOCO, 0):
            jogador1["proxima_direcao"] = (-TAMANHO_BLOCO, 0)
        elif tecla in (pygame.K_RIGHT, pygame.K_d) and jogador1["direcao"] != (-TAMANHO_BLOCO, 0):
            jogador1["proxima_direcao"] = (TAMANHO_BLOCO, 0)


async def rodar_jogo(indice_tema, recorde):
    tema = TEMAS[indice_tema]
    dificuldade = DIFICULDADES[CONFIG["dificuldade"]]
    velocidade_base = min(
        max(CONFIG["velocidade_inicial"] + dificuldade["modificador_velocidade"], VELOCIDADE_INICIAL_MIN),
        VELOCIDADE_MAXIMA,
    )
    modo = CONFIG["modo_jogo"]

    if modo == "2 Jogadores":
        cobras = [
            criar_cobra((100, 200), (TAMANHO_BLOCO, 0), "jogador1"),
            criar_cobra((480, 200), (-TAMANHO_BLOCO, 0), "jogador2"),
        ]
    elif modo == "Jogador vs Bot":
        cobras = [
            criar_cobra((100, 200), (TAMANHO_BLOCO, 0), "jogador1"),
            criar_cobra((480, 200), (-TAMANHO_BLOCO, 0), "bot"),
        ]
    else:
        cobras = [criar_cobra((LARGURA // 2, ALTURA // 2), (TAMANHO_BLOCO, 0), "jogador1")]

    ocupados_iniciais = []
    for cobra in cobras:
        ocupados_iniciais += cobra["corpo"]

    if CONFIG["mapa_personalizado"]:
        mapa = carregar_mapa_personalizado()
        obstaculos = [celula for celula in mapa if celula not in ocupados_iniciais]
    else:
        obstaculos = gerar_obstaculos(dificuldade["obstaculos"], ocupados_iniciais)

    comida, comida_especial = gerar_comida(ocupados_iniciais + obstaculos)

    pausado = False
    particulas = []
    tempo_acumulado = 0.0
    fase_atual = 1
    aviso_fase_ate = 0

    while True:
        dt = relogio.tick(FPS_RENDER) / 1000.0

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
            tela_de_pausa()
            await asyncio.sleep(0)
            continue

        tempo_acumulado += dt

        while any(c["viva"] for c in cobras):
            pontuacao_max = max(c["pontuacao"] for c in cobras)
            velocidade_atual = min(velocidade_base + pontuacao_max // PONTOS_POR_NIVEL, VELOCIDADE_MAXIMA)
            intervalo = 1.0 / velocidade_atual
            if tempo_acumulado < intervalo:
                break
            tempo_acumulado -= intervalo

            for cobra in cobras:
                if cobra["viva"]:
                    cobra["corpo_anterior"] = list(cobra["corpo"])

            for cobra in cobras:
                if not cobra["viva"]:
                    continue
                if cobra["controlador"] == "bot":
                    perigos = set(obstaculos)
                    for outra in cobras:
                        perigos.update(outra["corpo"])
                    cobra["proxima_direcao"] = escolher_direcao_bot(
                        cobra["corpo"][0], cobra["direcao"], comida, perigos
                    )
                cobra["direcao"] = cobra["proxima_direcao"]

            novas_cabecas = {}
            for cobra in cobras:
                if not cobra["viva"]:
                    continue
                cabeca = cobra["corpo"][0]
                d = cobra["direcao"]
                nova = (cabeca[0] + d[0], cabeca[1] + d[1])
                if CONFIG["parede_atravessavel"]:
                    nova = (nova[0] % LARGURA, nova[1] % ALTURA)
                novas_cabecas[id(cobra)] = nova

            agora = pygame.time.get_ticks()
            for cobra in cobras:
                if not cobra["viva"]:
                    continue
                nova = novas_cabecas[id(cobra)]
                protegido = agora < cobra["escudo_ate"]
                morreu = False
                if not CONFIG["parede_atravessavel"] and (
                    nova[0] < 0 or nova[0] >= LARGURA or nova[1] < 0 or nova[1] >= ALTURA
                ):
                    morreu = True
                elif not protegido and nova in obstaculos:
                    morreu = True
                elif not protegido and nova in cobra["corpo"]:
                    morreu = True
                else:
                    for outra in cobras:
                        if outra is cobra or not outra["viva"]:
                            continue
                        if not protegido and nova in outra["corpo"]:
                            morreu = True
                        if nova == novas_cabecas.get(id(outra)):
                            morreu = True
                if morreu:
                    cobra["viva"] = False
                    SOM_COLIDIR.play()

            comida_comida = False
            for cobra in cobras:
                if not cobra["viva"]:
                    continue
                nova = novas_cabecas[id(cobra)]
                cobra["corpo"].insert(0, nova)
                if nova == comida:
                    comida_comida = True
                    if comida_especial:
                        cobra["pontuacao"] += 5
                        cobra["escudo_ate"] = agora + DURACAO_ESCUDO_MS
                        particulas += criar_particulas(*comida, DOURADO, 20)
                    else:
                        cobra["pontuacao"] += 1
                        particulas += criar_particulas(*comida, tema["comida"], 12)
                    SOM_COMER.play()
                else:
                    cobra["corpo"].pop()

            if comida_comida:
                ocupados = list(obstaculos)
                for cobra in cobras:
                    ocupados += cobra["corpo"]
                comida, comida_especial = gerar_comida(ocupados)

            pontuacao_max = max(c["pontuacao"] for c in cobras)
            nova_fase = calcular_fase(pontuacao_max)
            if nova_fase > fase_atual:
                qtd_novos = obstaculos_extra_da_fase(nova_fase) - obstaculos_extra_da_fase(fase_atual)
                if qtd_novos > 0:
                    ocupados = list(obstaculos) + [comida]
                    for cobra in cobras:
                        ocupados += cobra["corpo"]
                    obstaculos += gerar_obstaculos(qtd_novos, ocupados)
                fase_atual = nova_fase
                aviso_fase_ate = pygame.time.get_ticks() + 1500
                SOM_SELECIONAR.play()

        if not any(c["viva"] for c in cobras):
            return cobras

        for particula in particulas:
            particula.atualizar(dt)
        particulas = [p for p in particulas if p.viva()]

        pontuacao_max = max(c["pontuacao"] for c in cobras)
        velocidade_atual = min(velocidade_base + pontuacao_max // PONTOS_POR_NIVEL, VELOCIDADE_MAXIMA)
        intervalo = 1.0 / velocidade_atual
        progresso = min(tempo_acumulado / intervalo, 1.0) if intervalo > 0 else 1.0

        desenhar_jogo(
            tema, cobras, progresso, comida, comida_especial, obstaculos,
            recorde, velocidade_atual, fase_atual, aviso_fase_ate, particulas,
        )

        await asyncio.sleep(0)


async def main():
    recorde = carregar_recorde()
    carregar_config()
    ranking = carregar_ranking()
    indice_tema = 0

    while True:
        indice_tema = await menu_principal(indice_tema, recorde)

        continuar = True
        while continuar:
            cobras = await rodar_jogo(indice_tema, recorde)
            modo = CONFIG["modo_jogo"]

            if modo != "2 Jogadores":
                pontuacao = cobras[0]["pontuacao"]
                if pontuacao > recorde:
                    recorde = pontuacao
                    salvar_recorde(recorde)
                if pontuacao > 0 and entra_no_ranking(ranking, pontuacao):
                    nome = await tela_entrada_nome(pontuacao)
                    ranking = adicionar_ao_ranking(ranking, nome, pontuacao)
                    salvar_ranking(ranking)

            escolha = await tela_de_fim(cobras, modo, recorde)
            if escolha == "menu":
                continuar = False
            elif escolha == "jogar":
                continue


if __name__ == "__main__":
    asyncio.run(main())