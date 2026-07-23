import pygame
import random
import sys

pygame.init()

# ---------- Configurações básicas ----------
LARGURA, ALTURA = 600, 400
TAMANHO_BLOCO = 20
VELOCIDADE = 10  # quadros por segundo (quanto maior, mais rápido)

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERDE = (0, 200, 0)
VERDE_ESCURO = (0, 120, 0)
VERMELHO = (200, 0, 0)
CINZA = (40, 40, 40)

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo da Cobrinha")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 24)
fonte_grande = pygame.font.SysFont("arial", 48)


def desenhar_texto(texto, fonte, cor, x, y, centralizado=False):
    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)


def gerar_comida(cobra):
    while True:
        pos = (
            random.randrange(0, LARGURA, TAMANHO_BLOCO),
            random.randrange(0, ALTURA, TAMANHO_BLOCO),
        )
        if pos not in cobra:
            return pos


def tela_de_fim(pontuacao):
    tela.fill(PRETO)
    desenhar_texto("Você perdeu!", fonte_grande, VERMELHO, LARGURA // 2, ALTURA // 2 - 40, centralizado=True)
    desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, LARGURA // 2, ALTURA // 2 + 10, centralizado=True)
    desenhar_texto("Pressione R para jogar novamente ou Q para sair", fonte, BRANCO, LARGURA // 2, ALTURA // 2 + 50, centralizado=True)
    pygame.display.update()

    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_r:
                    return True
                if evento.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
    return False


def rodar_jogo():
    cobra = [(LARGURA // 2, ALTURA // 2)]
    direcao = (TAMANHO_BLOCO, 0)
    proxima_direcao = direcao
    comida = gerar_comida(cobra)
    pontuacao = 0

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w) and direcao != (0, TAMANHO_BLOCO):
                    proxima_direcao = (0, -TAMANHO_BLOCO)
                elif evento.key in (pygame.K_DOWN, pygame.K_s) and direcao != (0, -TAMANHO_BLOCO):
                    proxima_direcao = (0, TAMANHO_BLOCO)
                elif evento.key in (pygame.K_LEFT, pygame.K_a) and direcao != (TAMANHO_BLOCO, 0):
                    proxima_direcao = (-TAMANHO_BLOCO, 0)
                elif evento.key in (pygame.K_RIGHT, pygame.K_d) and direcao != (-TAMANHO_BLOCO, 0):
                    proxima_direcao = (TAMANHO_BLOCO, 0)

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
            return pontuacao

        # Colisão com o próprio corpo
        if nova_cabeca in cobra:
            return pontuacao

        cobra.insert(0, nova_cabeca)

        if nova_cabeca == comida:
            pontuacao += 1
            comida = gerar_comida(cobra)
        else:
            cobra.pop()

        # ---------- Desenho ----------
        tela.fill(PRETO)

        # Grade sutil de fundo (opcional, ajuda a visualizar o grid)
        for x in range(0, LARGURA, TAMANHO_BLOCO):
            pygame.draw.line(tela, CINZA, (x, 0), (x, ALTURA))
        for y in range(0, ALTURA, TAMANHO_BLOCO):
            pygame.draw.line(tela, CINZA, (0, y), (LARGURA, y))

        # Comida
        pygame.draw.rect(tela, VERMELHO, (*comida, TAMANHO_BLOCO, TAMANHO_BLOCO))

        # Cobra
        for i, segmento in enumerate(cobra):
            cor = VERDE_ESCURO if i == 0 else VERDE
            pygame.draw.rect(tela, cor, (*segmento, TAMANHO_BLOCO, TAMANHO_BLOCO))

        # Pontuação
        desenhar_texto(f"Pontuação: {pontuacao}", fonte, BRANCO, 10, 10)

        pygame.display.update()
        relogio.tick(VELOCIDADE)


def main():
    jogar_novamente = True
    while jogar_novamente:
        pontuacao = rodar_jogo()
        jogar_novamente = tela_de_fim(pontuacao)


if __name__ == "__main__":
    main()
