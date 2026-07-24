import pygame
import numpy as np
import random
import sys
import os
import math

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

# Cores gerais (usadas fora dos temas)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (40, 40, 40)
AMARELO = (230, 200, 40)
DOURADO = (255, 215, 0)

CAMINHO_BASE = os.path.dirname(os.path.abspath(__file__))
CAMINHO_RECORDE = os.path.join(CAMINHO_BASE, "recorde.txt")
CAMINHO_CONFIG = os.path.join(CAMINHO_BASE, "config.txt")

# Configurações ajustáveis pelo jogador
CONFIG = {
    "volume": 0.7,
    "velocidade_inicial": 8,
    "parede_atravessavel": False,
    "dificuldade": "Médio",
}

# Cada dificuldade define quantos obstáculos existem no mapa e um ajuste na velocidade base
DIFICULDADES = {
    "Fácil": {"obstaculos": 0, "modificador_velocidade": -2},
    "Médio": {"obstaculos": 5, "modificador_velocidade": 0},
    "Difícil": {"obstaculos": 10, "modificador_velocidade": 3},
}
LISTA_DIFICULDADES = ["Fácil", "Médio", "Difícil"]

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


# ---------- Configurações (volume, velocidade, parede, dificuldade) ----------
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
        except (ValueError, OSError, IndexError):
            pass
    aplicar_volume()


def salvar_config():
    with open(CAMINHO_CONFIG, "w") as arquivo:
        arquivo.write(
            f"{CONFIG['volume']}\n{CONFIG['velocidade_inicial']}\n"
            f"{1 if CONFIG['parede_atravessavel'] else 0}\n{CONFIG['dificuldade']}"
        )


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


# ---------- Menu principal ----------
def menu_principal(indice_tema, recorde):
    opcoes = ["Jogar", "Tema", "Configurações", "Sair"]
    selecionado = 0

    while True:
        tema = TEMAS[indice_tema]
        tela.fill(PRETO)
        desenhar_texto("JOGO DA COBRINHA", fonte_grande, AMARELO, LARGURA // 2, 55, centralizado=True)
        desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, LARGURA // 2, 100, centralizado=True)
        desenhar_texto(
            f"Dificuldade atual: {CONFIG['dificuldade']}", fonte, (170, 170, 170), LARGURA // 2, 125, centralizado=True
        )

        for i, opcao in enumerate(opcoes):
            cor = AMARELO if i == selecionado else BRANCO
            texto = opcao
            if opcao == "Tema":
                texto = f"< Tema: {tema['nome']} >"
            desenhar_texto(texto, fonte, cor, LARGURA // 2, 175 + i * 42, centralizado=True)

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
    opcoes = ["Volume", "Velocidade inicial", "Parede", "Dificuldade", "Voltar"]
    selecionado = 0

    while True:
        tela.fill(PRETO)
        desenhar_texto("CONFIGURAÇÕES", fonte_grande, AMARELO, LARGURA // 2, 50, centralizado=True)

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
            else:
                texto = opcao
            desenhar_texto(texto, fonte, cor, LARGURA // 2, 115 + i * 40, centralizado=True)

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
                    else:
                        alterou = False
                    if alterou:
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


def interpolar_posicao(origem, destino, progresso):
    # Evita um "arrastão" visual quando a cobra atravessa de um lado ao outro da tela
    dx = destino[0] - origem[0]
    dy = destino[1] - origem[1]
    if abs(dx) > TAMANHO_BLOCO * 1.5 or abs(dy) > TAMANHO_BLOCO * 1.5:
        return destino
    return (origem[0] + dx * progresso, origem[1] + dy * progresso)


def desenhar_jogo(
    tema, cobra, cobra_anterior, progresso, comida, comida_especial, obstaculos,
    pontuacao, recorde, velocidade_atual, protegido, particulas,
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

    for i, segmento_novo in enumerate(cobra):
        origem = cobra_anterior[i] if i < len(cobra_anterior) else segmento_novo
        x, y = interpolar_posicao(origem, segmento_novo, progresso)
        cor = tema["cabeca"] if i == 0 else tema["corpo"]
        pygame.draw.rect(tela, cor, (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO))
        if protegido:
            pygame.draw.rect(tela, DOURADO, (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO), 2)

    desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, 10, 10)
    desenhar_texto(f"Recorde: {recorde}", fonte, BRANCO, 10, 35)
    desenhar_texto("P/ESC: pausar", fonte, (150, 150, 150), LARGURA - 150, 10)

    if velocidade_atual >= VELOCIDADE_MAXIMA:
        desenhar_texto("Velocidade máxima!", fonte, AMARELO, 10, 60)
    else:
        pontos_restantes = PONTOS_POR_NIVEL - (pontuacao % PONTOS_POR_NIVEL)
        desenhar_texto(f"Próx. velocidade em {pontos_restantes} ponto(s)", fonte, (150, 150, 150), 10, 60)
        progresso_barra = 1 - (pontos_restantes / PONTOS_POR_NIVEL)
        largura_barra = 150
        pygame.draw.rect(tela, (60, 60, 60), (10, 85, largura_barra, 8))
        pygame.draw.rect(tela, AMARELO, (10, 85, int(largura_barra * progresso_barra), 8))

    if protegido:
        desenhar_texto("Escudo ativo!", fonte, DOURADO, 10, 105)

    pygame.display.update()


def rodar_jogo(indice_tema, recorde):
    tema = TEMAS[indice_tema]
    dificuldade = DIFICULDADES[CONFIG["dificuldade"]]
    velocidade_base = min(
        max(CONFIG["velocidade_inicial"] + dificuldade["modificador_velocidade"], VELOCIDADE_INICIAL_MIN),
        VELOCIDADE_MAXIMA,
    )

    cobra = [(LARGURA // 2, ALTURA // 2)]
    cobra_anterior = list(cobra)
    direcao = (TAMANHO_BLOCO, 0)
    proxima_direcao = direcao

    obstaculos = gerar_obstaculos(dificuldade["obstaculos"], cobra)
    comida, comida_especial = gerar_comida(cobra + obstaculos)

    pontuacao = 0
    pausado = False
    escudo_ate = 0  # timestamp (ms) até quando a cobra fica protegida por comida especial
    particulas = []
    tempo_acumulado = 0.0

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
            continue

        velocidade_atual = min(velocidade_base + pontuacao // PONTOS_POR_NIVEL, VELOCIDADE_MAXIMA)
        intervalo = 1.0 / velocidade_atual

        tempo_acumulado += dt
        resultado_colisao = None

        while tempo_acumulado >= intervalo:
            tempo_acumulado -= intervalo
            cobra_anterior = list(cobra)
            direcao = proxima_direcao
            cabeca_atual = cobra[0]
            nova_cabeca = (cabeca_atual[0] + direcao[0], cabeca_atual[1] + direcao[1])

            if CONFIG["parede_atravessavel"]:
                nova_cabeca = (nova_cabeca[0] % LARGURA, nova_cabeca[1] % ALTURA)
            elif (
                nova_cabeca[0] < 0
                or nova_cabeca[0] >= LARGURA
                or nova_cabeca[1] < 0
                or nova_cabeca[1] >= ALTURA
            ):
                resultado_colisao = "parede"
                break

            agora = pygame.time.get_ticks()
            protegido_neste_passo = agora < escudo_ate

            if nova_cabeca in cobra and not protegido_neste_passo:
                resultado_colisao = "corpo"
                break

            if nova_cabeca in obstaculos and not protegido_neste_passo:
                resultado_colisao = "obstaculo"
                break

            cobra.insert(0, nova_cabeca)

            if nova_cabeca == comida:
                if comida_especial:
                    pontuacao += 5
                    escudo_ate = agora + DURACAO_ESCUDO_MS
                    particulas += criar_particulas(*comida, DOURADO, 20)
                else:
                    pontuacao += 1
                    particulas += criar_particulas(*comida, tema["comida"], 12)
                SOM_COMER.play()
                comida, comida_especial = gerar_comida(cobra + obstaculos)
            else:
                cobra.pop()

        if resultado_colisao:
            SOM_COLIDIR.play()
            return pontuacao

        for particula in particulas:
            particula.atualizar(dt)
        particulas = [p for p in particulas if p.viva()]

        progresso = min(tempo_acumulado / intervalo, 1.0) if intervalo > 0 else 1.0
        protegido = pygame.time.get_ticks() < escudo_ate
        desenhar_jogo(
            tema, cobra, cobra_anterior, progresso, comida, comida_especial, obstaculos,
            pontuacao, recorde, velocidade_atual, protegido, particulas,
        )


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