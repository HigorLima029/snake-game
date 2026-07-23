import pygame
import numpy as np
import random
import sys
import os

pygame.init()
pygame.mixer.init()

# ---------- Configurações básicas ----------
LARGURA, ALTURA = 600, 400
TAMANHO_BLOCO = 20
VELOCIDADE_MAXIMA = 20
PONTOS_POR_NIVEL = 3  # a cada X pontos, a velocidade aumenta 1
VELOCIDADE_INICIAL_MIN = 4
VELOCIDADE_INICIAL_MAX = 15

# Cores gerais (usadas fora dos temas)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (40, 40, 40)
AMARELO = (230, 200, 40)

CAMINHO_BASE = os.path.dirname(os.path.abspath(__file__))
CAMINHO_RECORDE = os.path.join(CAMINHO_BASE, "recorde.txt")
CAMINHO_CONFIG = os.path.join(CAMINHO_BASE, "config.txt")

# Configurações ajustáveis pelo jogador (volume e velocidade inicial)
CONFIG = {"volume": 0.7, "velocidade_inicial": 8}

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo da Cobrinha")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 22)
fonte_grande = pygame.font.SysFont("arial", 46)

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


# ---------- Configurações (volume e velocidade inicial) ----------
def carregar_config():
    if os.path.exists(CAMINHO_CONFIG):
        try:
            with open(CAMINHO_CONFIG, "r") as arquivo:
                linhas = arquivo.read().strip().splitlines()
                volume = float(linhas[0])
                velocidade_inicial = int(linhas[1])
                CONFIG["volume"] = min(max(volume, 0.0), 1.0)
                CONFIG["velocidade_inicial"] = min(
                    max(velocidade_inicial, VELOCIDADE_INICIAL_MIN), VELOCIDADE_INICIAL_MAX
                )
        except (ValueError, OSError, IndexError):
            pass
    aplicar_volume()


def salvar_config():
    with open(CAMINHO_CONFIG, "w") as arquivo:
        arquivo.write(f"{CONFIG['volume']}\n{CONFIG['velocidade_inicial']}")


def aplicar_volume():
    for som in (SOM_COMER, SOM_COLIDIR, SOM_SELECIONAR):
        som.set_volume(CONFIG["volume"])


def desenhar_texto(texto, fonte_usada, cor, x, y, centralizado=False):
    superficie = fonte_usada.render(texto, True, cor)
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)
    return rect


def gerar_comida(cobra):
    while True:
        pos = (
            random.randrange(0, LARGURA, TAMANHO_BLOCO),
            random.randrange(0, ALTURA, TAMANHO_BLOCO),
        )
        if pos not in cobra:
            return pos


# ---------- Menu principal ----------
def menu_principal(indice_tema, recorde):
    opcoes = ["Jogar", "Tema", "Configurações", "Sair"]
    selecionado = 0

    while True:
        tema = TEMAS[indice_tema]
        tela.fill(PRETO)
        desenhar_texto("JOGO DA COBRINHA", fonte_grande, AMARELO, LARGURA // 2, 60, centralizado=True)
        desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, LARGURA // 2, 110, centralizado=True)

        for i, opcao in enumerate(opcoes):
            cor = AMARELO if i == selecionado else BRANCO
            texto = opcao
            if opcao == "Tema":
                texto = f"< Tema: {tema['nome']} >"
            desenhar_texto(texto, fonte, cor, LARGURA // 2, 170 + i * 42, centralizado=True)

        desenhar_texto(
            "seta cima/baixo: navegar   esquerda/direita: trocar tema   Enter: confirmar",
            fonte,
            (150, 150, 150),
            LARGURA // 2,
            ALTURA - 20,
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
                        tela_configuracoes()
                    elif opcoes[selecionado] == "Sair":
                        pygame.quit()
                        sys.exit()

        relogio.tick(30)


def tela_configuracoes():
    opcoes = ["Volume", "Velocidade inicial", "Voltar"]
    selecionado = 0

    while True:
        tela.fill(PRETO)
        desenhar_texto("CONFIGURAÇÕES", fonte_grande, AMARELO, LARGURA // 2, 60, centralizado=True)

        for i, opcao in enumerate(opcoes):
            cor = AMARELO if i == selecionado else BRANCO
            if opcao == "Volume":
                percentual = int(CONFIG["volume"] * 100)
                texto = f"< Volume: {percentual}% >"
            elif opcao == "Velocidade inicial":
                texto = f"< Velocidade inicial: {CONFIG['velocidade_inicial']} >"
            else:
                texto = opcao
            desenhar_texto(texto, fonte, cor, LARGURA // 2, 150 + i * 45, centralizado=True)

        desenhar_texto(
            "esquerda/direita: ajustar   Enter/ESC: voltar",
            fonte,
            (150, 150, 150),
            LARGURA // 2,
            ALTURA - 20,
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
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    if opcoes[selecionado] == "Volume":
                        CONFIG["volume"] = round(max(CONFIG["volume"] - 0.1, 0.0), 2)
                        aplicar_volume()
                        SOM_SELECIONAR.play()
                        salvar_config()
                    elif opcoes[selecionado] == "Velocidade inicial":
                        CONFIG["velocidade_inicial"] = max(
                            CONFIG["velocidade_inicial"] - 1, VELOCIDADE_INICIAL_MIN
                        )
                        SOM_SELECIONAR.play()
                        salvar_config()
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    if opcoes[selecionado] == "Volume":
                        CONFIG["volume"] = round(min(CONFIG["volume"] + 0.1, 1.0), 2)
                        aplicar_volume()
                        SOM_SELECIONAR.play()
                        salvar_config()
                    elif opcoes[selecionado] == "Velocidade inicial":
                        CONFIG["velocidade_inicial"] = min(
                            CONFIG["velocidade_inicial"] + 1, VELOCIDADE_INICIAL_MAX
                        )
                        SOM_SELECIONAR.play()
                        salvar_config()
                elif evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    if opcoes[selecionado] == "Voltar" or evento.key == pygame.K_ESCAPE:
                        return

        relogio.tick(30)


def tela_de_pausa():
    overlay = pygame.Surface((LARGURA, ALTURA))
    overlay.set_alpha(180)
    overlay.fill(PRETO)
    tela.blit(overlay, (0, 0))
    desenhar_texto("PAUSADO", fonte_grande, AMARELO, LARGURA // 2, ALTURA // 2 - 20, centralizado=True)
    desenhar_texto("Pressione P ou ESC para continuar", fonte, BRANCO, LARGURA // 2, ALTURA // 2 + 30, centralizado=True)
    pygame.display.update()


def tela_de_fim(pontuacao, recorde, bateu_recorde):
    tela.fill(PRETO)
    desenhar_texto("Você perdeu!", fonte_grande, (200, 40, 40), LARGURA // 2, ALTURA // 2 - 60, centralizado=True)
    desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, LARGURA // 2, ALTURA // 2 - 10, centralizado=True)
    if bateu_recorde:
        desenhar_texto("Novo recorde!", fonte, AMARELO, LARGURA // 2, ALTURA // 2 + 20, centralizado=True)
    else:
        desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, LARGURA // 2, ALTURA // 2 + 20, centralizado=True)
    desenhar_texto(
        "R: jogar de novo    M: menu    Q: sair",
        fonte,
        (180, 180, 180),
        LARGURA // 2,
        ALTURA // 2 + 60,
        centralizado=True,
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


def rodar_jogo(indice_tema, recorde):
    tema = TEMAS[indice_tema]
    cobra = [(LARGURA // 2, ALTURA // 2)]
    direcao = (TAMANHO_BLOCO, 0)
    proxima_direcao = direcao
    comida = gerar_comida(cobra)
    pontuacao = 0
    pausado = False

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_ESCAPE, pygame.K_p):
                    pausado = not pausado
                elif not pausado:
                    if evento.key in (pygame.K_UP, pygame.K_w) and direcao != (0, TAMANHO_BLOCO):
                        proxima_direcao = (0, -TAMANHO_BLOCO)
                    elif evento.key in (pygame.K_DOWN, pygame.K_s) and direcao != (0, -TAMANHO_BLOCO):
                        proxima_direcao = (0, TAMANHO_BLOCO)
                    elif evento.key in (pygame.K_LEFT, pygame.K_a) and direcao != (TAMANHO_BLOCO, 0):
                        proxima_direcao = (-TAMANHO_BLOCO, 0)
                    elif evento.key in (pygame.K_RIGHT, pygame.K_d) and direcao != (-TAMANHO_BLOCO, 0):
                        proxima_direcao = (TAMANHO_BLOCO, 0)

        if pausado:
            tela_de_pausa()
            relogio.tick(15)
            continue

        direcao = proxima_direcao
        cabeca_atual = cobra[0]
        nova_cabeca = (cabeca_atual[0] + direcao[0], cabeca_atual[1] + direcao[1])

        # Colisão com a parede
        if (
            nova_cabeca[0] < 0
            or nova_cabeca[0] >= LARGURA
            or nova_cabeca[1] < 0
            or nova_cabeca[1] >= ALTURA
        ):
            SOM_COLIDIR.play()
            return pontuacao

        # Colisão com o próprio corpo
        if nova_cabeca in cobra:
            SOM_COLIDIR.play()
            return pontuacao

        cobra.insert(0, nova_cabeca)

        if nova_cabeca == comida:
            pontuacao += 1
            SOM_COMER.play()
            comida = gerar_comida(cobra)
        else:
            cobra.pop()

        # ---------- Desenho ----------
        tela.fill(tema["fundo"])

        for x in range(0, LARGURA, TAMANHO_BLOCO):
            pygame.draw.line(tela, tema["grade"], (x, 0), (x, ALTURA))
        for y in range(0, ALTURA, TAMANHO_BLOCO):
            pygame.draw.line(tela, tema["grade"], (0, y), (LARGURA, y))

        pygame.draw.rect(tela, tema["comida"], (*comida, TAMANHO_BLOCO, TAMANHO_BLOCO))

        for i, segmento in enumerate(cobra):
            cor = tema["cabeca"] if i == 0 else tema["corpo"]
            pygame.draw.rect(tela, cor, (*segmento, TAMANHO_BLOCO, TAMANHO_BLOCO))

        desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, 10, 10)
        desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, 10, 35)
        desenhar_texto("P/ESC: pausar", fonte, (150, 150, 150), LARGURA - 150, 10)

        velocidade_atual = min(
            CONFIG["velocidade_inicial"] + pontuacao // PONTOS_POR_NIVEL, VELOCIDADE_MAXIMA
        )

        # Contador visual do próximo aumento de velocidade
        if velocidade_atual >= VELOCIDADE_MAXIMA:
            desenhar_texto("Velocidade máxima!", fonte, AMARELO, 10, 60)
        else:
            pontos_restantes = PONTOS_POR_NIVEL - (pontuacao % PONTOS_POR_NIVEL)
            desenhar_texto(f"Próx. velocidade em {pontos_restantes} ponto(s)", fonte, (150, 150, 150), 10, 60)
            progresso = 1 - (pontos_restantes / PONTOS_POR_NIVEL)
            largura_barra = 150
            pygame.draw.rect(tela, (60, 60, 60), (10, 85, largura_barra, 8))
            pygame.draw.rect(tela, AMARELO, (10, 85, int(largura_barra * progresso), 8))

        pygame.display.update()

        relogio.tick(velocidade_atual)


def main():
    recorde = carregar_recorde()
    carregar_config()
    indice_tema = 0

    while True:
        indice_tema = menu_principal(indice_tema, recorde)

        continuar = True
        while continuar:
            pontuacao = rodar_jogo(indice_tema, recorde)

            bateu_recorde = pontuacao > recorde
            if bateu_recorde:
                recorde = pontuacao
                salvar_recorde(recorde)

            escolha = tela_de_fim(pontuacao, recorde, bateu_recorde)
            if escolha == "menu":
                continuar = False
            elif escolha == "jogar":
                continue


if __name__ == "__main__":
    main()