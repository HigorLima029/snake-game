"""Testes para cobrinha.config: persistência de recorde, config, ranking e mapa."""
from cobrinha import config


def test_recorde_roundtrip(tmp_path, monkeypatch):
    caminho = tmp_path / "recorde.txt"
    monkeypatch.setattr(config, "CAMINHO_RECORDE", str(caminho))

    assert config.carregar_recorde() == 0  # arquivo ainda não existe

    config.salvar_recorde(42)
    assert config.carregar_recorde() == 42


def test_recorde_arquivo_corrompido_retorna_zero(tmp_path, monkeypatch):
    caminho = tmp_path / "recorde.txt"
    caminho.write_text("isso não é um número")
    monkeypatch.setattr(config, "CAMINHO_RECORDE", str(caminho))

    assert config.carregar_recorde() == 0


def test_config_roundtrip(tmp_path, monkeypatch):
    caminho = tmp_path / "config.txt"
    monkeypatch.setattr(config, "CAMINHO_CONFIG", str(caminho))

    monkeypatch.setitem(config.CONFIG, "volume", 0.5)
    monkeypatch.setitem(config.CONFIG, "velocidade_inicial", 10)
    monkeypatch.setitem(config.CONFIG, "parede_atravessavel", True)
    monkeypatch.setitem(config.CONFIG, "dificuldade", "Difícil")
    monkeypatch.setitem(config.CONFIG, "modo_jogo", "Jogador vs Bot")
    monkeypatch.setitem(config.CONFIG, "mapa_personalizado", True)

    config.salvar_config()

    # simula reiniciar o jogo com valores diferentes e recarregar do arquivo
    monkeypatch.setitem(config.CONFIG, "volume", 0.0)
    monkeypatch.setitem(config.CONFIG, "velocidade_inicial", 4)
    monkeypatch.setitem(config.CONFIG, "parede_atravessavel", False)
    monkeypatch.setitem(config.CONFIG, "dificuldade", "Fácil")
    monkeypatch.setitem(config.CONFIG, "modo_jogo", "1 Jogador")
    monkeypatch.setitem(config.CONFIG, "mapa_personalizado", False)

    config.carregar_config()

    assert config.CONFIG["volume"] == 0.5
    assert config.CONFIG["velocidade_inicial"] == 10
    assert config.CONFIG["parede_atravessavel"] is True
    assert config.CONFIG["dificuldade"] == "Difícil"
    assert config.CONFIG["modo_jogo"] == "Jogador vs Bot"
    assert config.CONFIG["mapa_personalizado"] is True


def test_config_sem_arquivo_mantem_valores_atuais(tmp_path, monkeypatch):
    caminho = tmp_path / "config_inexistente.txt"
    monkeypatch.setattr(config, "CAMINHO_CONFIG", str(caminho))
    monkeypatch.setitem(config.CONFIG, "volume", 0.42)

    config.carregar_config()  # não deve levantar exceção nem alterar nada

    assert config.CONFIG["volume"] == 0.42


def test_entra_no_ranking_com_menos_de_dez_registros():
    ranking = [{"nome": "A", "pontuacao": 5}]
    assert config.entra_no_ranking(ranking, 1) is True


def test_entra_no_ranking_com_dez_registros():
    ranking = [{"nome": f"J{i}", "pontuacao": i} for i in range(10)]  # pontuações 0..9
    assert config.entra_no_ranking(ranking, 15) is True  # maior que o menor (0)
    assert config.entra_no_ranking(ranking, 0) is False  # empata com o menor, não supera


def test_adicionar_ao_ranking_ordena_e_limita_a_dez():
    ranking = []
    for i in range(12):
        ranking = config.adicionar_ao_ranking(ranking, f"J{i}", i)

    assert len(ranking) == 10
    pontuacoes = [registro["pontuacao"] for registro in ranking]
    assert pontuacoes == sorted(pontuacoes, reverse=True)
    assert min(pontuacoes) == 2  # os dois piores (0 e 1) ficaram de fora


def test_ranking_roundtrip(tmp_path, monkeypatch):
    caminho = tmp_path / "ranking.json"
    monkeypatch.setattr(config, "CAMINHO_RANKING", str(caminho))

    assert config.carregar_ranking() == []

    ranking = config.adicionar_ao_ranking([], "Higor", 99)
    config.salvar_ranking(ranking)

    assert config.carregar_ranking() == ranking


def test_mapa_personalizado_roundtrip(tmp_path, monkeypatch):
    caminho = tmp_path / "mapa.txt"
    monkeypatch.setattr(config, "CAMINHO_MAPA", str(caminho))

    assert config.carregar_mapa_personalizado() == []

    celulas = [(20, 20), (40, 40), (60, 80)]
    config.salvar_mapa_personalizado(celulas)

    assert config.carregar_mapa_personalizado() == celulas
