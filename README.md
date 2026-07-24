# Jogo da Cobrinha (Snake)

Versão simples do clássico jogo da cobrinha, feita em Python com [pygame](https://www.pygame.org/).

## Como rodar

1. Instale o pygame:
   ```bash
   pip install pygame
   ```
2. Execute o jogo:
   ```bash
   python cobrinha.py
   ```

## Controles

- Setas do teclado ou `W A S D` para mover
- Ao perder: `R` para jogar novamente, `Q` para sair

## Controles adicionais

- `P` ou `ESC` durante o jogo: pausa / despausa
- No menu: setas para navegar, `←`/`→` para trocar de tema, `Enter` para confirmar
- Na tela de fim de jogo: `R` joga de novo, `M` volta ao menu, `Q` sai

## Como está estruturado hoje

- `menu_principal()` tela inicial com opções Jogar / Tema / Sair
- `gerar_tom()` gera os efeitos sonoros na hora (sem precisar de arquivos de áudio externos)
- `carregar_recorde()` / `salvar_recorde()` leem e gravam o recorde em `recorde.txt` (criado ao lado do script)
- `rodar_jogo()` contém o loop principal: entrada do usuário, pausa, movimento, colisões e desenho
- `tela_de_pausa()` mostra um overlay semitransparente com "PAUSADO"
- `tela_de_fim()` mostra a pontuação final, se bateu recorde, e as opções de jogar de novo/menu/sair
- Velocidade aumenta a cada `PONTOS_POR_NIVEL` pontos, até um teto (`VELOCIDADE_MAXIMA`)
- 4 temas prontos (Clássico, Neon, Gelo, Deserto) em `TEMAS`, escolhidos no menu
- `tela_configuracoes()` ajusta volume (0-100%), velocidade inicial (4-15), tipo de parede (sólida/atravessável) e dificuldade, salvando tudo em `config.txt`
- Durante o jogo, um texto + barra de progresso mostram quantos pontos faltam para o próximo aumento de velocidade
- Dificuldade (Fácil / Médio / Difícil) define a quantidade de obstáculos no mapa e ajusta a velocidade base
- Parede "atravessável": a cobra sai de um lado da tela e reaparece do outro, em vez de morrer
- Obstáculos fixos (cinza) matam a cobra ao encostar, igual à colisão com o próprio corpo
- Comida dourada (~20% de chance) vale 5 pontos e dá um "escudo" de 3 segundos: durante esse tempo a cobra atravessa obstáculos e o próprio corpo sem morrer (indicado por um contorno dourado piscando)
- Movimento com animação suave: a cobra é desenhada interpolando entre a posição anterior e a nova a cada quadro, em vez de "pular" de bloco em bloco (o loop de desenho roda a 60 FPS, desacoplado da velocidade lógica do jogo)
- Partículas coloridas saem da comida ao ser comida (mais partículas e douradas na comida especial)

## Ideias de melhorias (pra ir escolhendo com calma)

### Já implementadas
- [x] Tela de menu inicial (Jogar / Sair)
- [x] Guardar e mostrar recorde (high score) em um arquivo local
- [x] Aumentar a velocidade gradualmente conforme a pontuação sobe
- [x] Sons de efeito (comer, colidir) com `pygame.mixer`
- [x] Pausar o jogo com `ESC` ou `P`
- [x] Cores/skins diferentes para a cobra (escolher tema)
- [x] Tela de configurações separada (volume, velocidade inicial) — salva em `config.txt`
- [x] Contador visual do próximo aumento de velocidade (texto + barra de progresso)

### Nível médio (implementadas)
- [x] Paredes "atravessáveis" (sair de um lado e entrar do outro, modo sem parede) — ajustável em Configurações
- [x] Obstáculos fixos no mapa que também matam a cobra — quantidade definida pela dificuldade
- [x] Comidas especiais (douradas, que valem mais pontos e dão um escudo temporário)
- [x] Modo dificuldade (fácil / médio / difícil) alterando velocidade e obstáculos
- [x] Animação suave de movimento (em vez de "pulos" de bloco em bloco)
- [x] Efeito visual quando a cobra come (partículas)

### Mais avançadas
- [ ] Modo dois jogadores (duas cobras no mesmo mapa)
- [ ] Cobra controlada por IA (bot) para comparar performance
- [ ] Editor de mapas simples (posicionar obstáculos antes de jogar)
- [ ] Sistema de fases/níveis com objetivos diferentes
- [ ] Ranking local com nomes dos jogadores (tipo os scores do ping pong)
- [ ] Versão web (usando algo como `pygbag` para rodar pygame no navegador)
