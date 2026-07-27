"""Configurações, constantes, tipos compartilhados e persistência em disco.

Este módulo é o primeiro a ser importado pelos demais: é ele quem chama
``pygame.init()`` e cria a janela, o relógio e as fontes usados em todo
o jogo.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple, TypedDict

import pygame

pygame.init()

# ---------- Tipos compartilhados ----------
Posicao = Tuple[int, int]
Direcao = Tuple[int, int]
Cor = Tuple[int, int, int]


class Tema(TypedDict):
    nome: str
    fundo: Cor
    grade: Cor
    cabeca: Cor
    corpo: Cor
    comida: Cor


class ConfiguracaoJogo(TypedDict):
    volume: float
    velocidade_inicial: int
    parede_atravessavel: bool
    dificuldade: str
    modo_jogo: str
    mapa_personalizado: bool


class RegistroRanking(TypedDict):
    nome: str
    pontuacao: int


# ---------- Configurações básicas ----------
LARGURA: int = 600
ALTURA: int = 400
TAMANHO_BLOCO: int = 20
VELOCIDADE_MAXIMA: int = 20
PONTOS_POR_NIVEL: int = 3  # a cada X pontos, a velocidade aumenta 1
VELOCIDADE_INICIAL_MIN: int = 4
VELOCIDADE_INICIAL_MAX: int = 15
FPS_RENDER: int = 60  # taxa de desenho (independente da velocidade lógica do jogo)
DURACAO_ESCUDO_MS: int = 3000  # tempo de efeito da comida especial
CHANCE_COMIDA_ESPECIAL: float = 0.2  # 20% de chance da comida nascer especial (dourada)
PONTOS_POR_FASE: int = 8
OBSTACULOS_POR_FASE: int = 2
OBSTACULOS_MAXIMOS_FASE: int = 12

# Cores gerais (usadas fora dos temas)
PRETO: Cor = (0, 0, 0)
BRANCO: Cor = (255, 255, 255)
CINZA: Cor = (40, 40, 40)
AMARELO: Cor = (230, 200, 40)
DOURADO: Cor = (255, 215, 0)
COR_CABECA_2: Cor = (230, 60, 210)
COR_CORPO_2: Cor = (150, 50, 150)

CAMINHO_BASE: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_RECORDE: str = os.path.join(CAMINHO_BASE, "recorde.txt")
CAMINHO_CONFIG: str = os.path.join(CAMINHO_BASE, "config.txt")
CAMINHO_MAPA: str = os.path.join(CAMINHO_BASE, "mapa_personalizado.txt")
CAMINHO_RANKING: str = os.path.join(CAMINHO_BASE, "ranking.json")

MODOS_JOGO: List[str] = ["1 Jogador", "2 Jogadores", "Jogador vs Bot"]

# Configurações ajustáveis pelo jogador (persistidas em CAMINHO_CONFIG)
CONFIG: ConfiguracaoJogo = {
    "volume": 0.7,
    "velocidade_inicial": 8,
    "parede_atravessavel": False,
    "dificuldade": "Médio",
    "modo_jogo": "1 Jogador",
    "mapa_personalizado": False,
}

# Cada dificuldade define quantos obstáculos existem no mapa e um ajuste na velocidade base
DIFICULDADES: Dict[str, Dict[str, int]] = {
    "Fácil": {"obstaculos": 0, "modificador_velocidade": -2},
    "Médio": {"obstaculos": 5, "modificador_velocidade": 0},
    "Difícil": {"obstaculos": 10, "modificador_velocidade": 3},
}
LISTA_DIFICULDADES: List[str] = ["Fácil", "Médio", "Difícil"]

DIRECOES: List[Direcao] = [
    (0, -TAMANHO_BLOCO), (0, TAMANHO_BLOCO), (-TAMANHO_BLOCO, 0), (TAMANHO_BLOCO, 0)
]

tela: pygame.Surface = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo da Cobrinha")
relogio: pygame.time.Clock = pygame.time.Clock()
fonte: pygame.font.Font = pygame.font.SysFont("arial", 20)
fonte_grande: pygame.font.Font = pygame.font.SysFont("arial", 44)

# ---------- Temas ----------
TEMAS: List[Tema] = [
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


# ---------- Recorde ----------
def carregar_recorde() -> int:
    if os.path.exists(CAMINHO_RECORDE):
        try:
            with open(CAMINHO_RECORDE, "r") as arquivo:
                return int(arquivo.read().strip())
        except (ValueError, OSError):
            return 0
    return 0


def salvar_recorde(pontuacao: int) -> None:
    with open(CAMINHO_RECORDE, "w") as arquivo:
        arquivo.write(str(pontuacao))


# ---------- Configurações (volume, velocidade, parede, dificuldade, modo, mapa) ----------
def carregar_config() -> None:
    """Carrega config.txt para dentro de CONFIG, se o arquivo existir.

    Não aplica o volume aos sons — quem chamar deve fazer isso explicitamente
    (ex.: ``sons.aplicar_volume(CONFIG["volume"])``), para este módulo não
    precisar depender do módulo de sons.
    """
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


def salvar_config() -> None:
    with open(CAMINHO_CONFIG, "w") as arquivo:
        arquivo.write(
            f"{CONFIG['volume']}\n{CONFIG['velocidade_inicial']}\n"
            f"{1 if CONFIG['parede_atravessavel'] else 0}\n{CONFIG['dificuldade']}\n"
            f"{CONFIG['modo_jogo']}\n{1 if CONFIG['mapa_personalizado'] else 0}"
        )


# ---------- Ranking local ----------
def carregar_ranking() -> List[RegistroRanking]:
    import json

    if os.path.exists(CAMINHO_RANKING):
        try:
            with open(CAMINHO_RANKING, "r") as arquivo:
                dados = json.load(arquivo)
                if isinstance(dados, list):
                    return dados
        except (ValueError, OSError):
            pass
    return []


def salvar_ranking(ranking: List[RegistroRanking]) -> None:
    import json

    with open(CAMINHO_RANKING, "w") as arquivo:
        json.dump(ranking, arquivo)


def entra_no_ranking(ranking: List[RegistroRanking], pontuacao: int) -> bool:
    if len(ranking) < 10:
        return True
    return pontuacao > min(registro["pontuacao"] for registro in ranking)


def adicionar_ao_ranking(
    ranking: List[RegistroRanking], nome: str, pontuacao: int
) -> List[RegistroRanking]:
    novo_ranking = ranking + [{"nome": nome, "pontuacao": pontuacao}]
    novo_ranking.sort(key=lambda registro: registro["pontuacao"], reverse=True)
    return novo_ranking[:10]


# ---------- Mapa personalizado ----------
def carregar_mapa_personalizado() -> List[Posicao]:
    celulas: List[Posicao] = []
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


def salvar_mapa_personalizado(celulas: List[Posicao]) -> None:
    with open(CAMINHO_MAPA, "w") as arquivo:
        for x, y in celulas:
            arquivo.write(f"{x},{y}\n")
