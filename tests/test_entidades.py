"""Testes para cobrinha.entidades: geração de mundo, partículas, IA do bot e fases."""
from cobrinha import config, entidades


def test_gerar_posicao_livre_evita_ocupados():
    ocupados = [(0, 0), (20, 0), (40, 0)]
    for _ in range(50):
        pos = entidades.gerar_posicao_livre(ocupados)
        assert pos not in ocupados
        assert 0 <= pos[0] < config.LARGURA
        assert 0 <= pos[1] < config.ALTURA


def test_gerar_obstaculos_sem_sobreposicao():
    ocupados = [(300, 200)]
    obstaculos = entidades.gerar_obstaculos(8, ocupados)
    assert len(obstaculos) == 8
    assert len(set(obstaculos)) == 8  # nenhum obstáculo repetido
    assert (300, 200) not in obstaculos


def test_gerar_comida_nao_sobrepoe_ocupados():
    ocupados = [(300, 200), (320, 200)]
    comida, especial = entidades.gerar_comida(ocupados)
    assert comida not in ocupados
    assert isinstance(especial, bool)


def test_criar_cobra_estado_inicial():
    cobra = entidades.criar_cobra((100, 100), (config.TAMANHO_BLOCO, 0), "jogador1")
    assert cobra.corpo == [(100, 100)]
    assert cobra.corpo_anterior == [(100, 100)]
    assert cobra.direcao == (config.TAMANHO_BLOCO, 0)
    assert cobra.pontuacao == 0
    assert cobra.viva is True
    assert cobra.controlador == "jogador1"


def test_particula_perde_vida_e_morre():
    particula = entidades.Particula(10, 10, (255, 0, 0))
    assert particula.viva()
    # avança tempo suficiente para a vida chegar a zero
    particula.atualizar(1.0)
    assert not particula.viva()


def test_interpolar_posicao_meio_do_caminho():
    origem, destino = (0, 0), (20, 0)
    x, y = entidades.interpolar_posicao(origem, destino, 0.5)
    assert (x, y) == (10.0, 0.0)


def test_interpolar_posicao_extremos():
    origem, destino = (0, 0), (20, 20)
    assert entidades.interpolar_posicao(origem, destino, 0.0) == (0.0, 0.0)
    assert entidades.interpolar_posicao(origem, destino, 1.0) == (20.0, 20.0)


def test_interpolar_posicao_detecta_wrap_de_parede():
    # Distância maior que 1.5 blocos: assume que é um "teleporte" (wrap) e não interpola
    origem = (config.LARGURA - config.TAMANHO_BLOCO, 0)
    destino = (0, 0)
    assert entidades.interpolar_posicao(origem, destino, 0.5) == destino


def test_escolher_direcao_bot_persegue_comida_sem_perigo():
    cabeca = (100, 100)
    direcao_atual = (config.TAMANHO_BLOCO, 0)
    comida = (100, 60)  # comida diretamente acima da cabeça
    direcao = entidades.escolher_direcao_bot(cabeca, direcao_atual, comida, set())
    assert direcao == (0, -config.TAMANHO_BLOCO)


def test_escolher_direcao_bot_evita_perigo_imediato():
    cabeca = (100, 100)
    direcao_atual = (config.TAMANHO_BLOCO, 0)
    comida = (100, 60)
    # bloqueia a célula diretamente acima: o bot não deve escolher subir
    perigos = {(100, 80)}
    direcao = entidades.escolher_direcao_bot(cabeca, direcao_atual, comida, perigos)
    assert direcao != (0, -config.TAMANHO_BLOCO)


def test_escolher_direcao_bot_nao_reverte_direcao():
    cabeca = (100, 100)
    direcao_atual = (config.TAMANHO_BLOCO, 0)  # indo para a direita
    comida = (0, 100)  # comida atrás da cobra
    # mesmo com a comida atrás, o bot não pode reverter direto (colidiria com o próprio pescoço)
    direcao = entidades.escolher_direcao_bot(cabeca, direcao_atual, comida, set())
    assert direcao != entidades.oposto(direcao_atual)


def test_oposto():
    assert entidades.oposto((config.TAMANHO_BLOCO, 0)) == (-config.TAMANHO_BLOCO, 0)
    assert entidades.oposto((0, -config.TAMANHO_BLOCO)) == (0, config.TAMANHO_BLOCO)


def test_calcular_fase():
    assert entidades.calcular_fase(0) == 1
    assert entidades.calcular_fase(config.PONTOS_POR_FASE) == 2
    assert entidades.calcular_fase(config.PONTOS_POR_FASE * 3) == 4


def test_obstaculos_extra_da_fase_respeita_teto():
    assert entidades.obstaculos_extra_da_fase(1) == 0
    assert entidades.obstaculos_extra_da_fase(2) == config.OBSTACULOS_POR_FASE
    assert entidades.obstaculos_extra_da_fase(1000) == config.OBSTACULOS_MAXIMOS_FASE
