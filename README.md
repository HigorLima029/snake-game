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

## Ideias de melhorias (pra ir escolhendo com calma)

### Já implementadas
- [x] Tela de menu inicial (Jogar / Sair)
- [x] Guardar e mostrar recorde (high score) em um arquivo local
- [x] Aumentar a velocidade gradualmente conforme a pontuação sobe
- [x] Sons de efeito (comer, colidir) com `pygame.mixer`
- [x] Pausar o jogo com `ESC` ou `P`
- [x] Cores/skins diferentes para a cobra (escolher tema)

### Fáceis de começar
- [ ] Tela de configurações separada (volume, velocidade inicial)
- [ ] Contador visual do próximo aumento de velocidade

### Nível médio
- [ ] Paredes "atravessáveis" (sair de um lado e entiar do outro, modo sem parede)
- [ ] Obstáculos fixos no mapa que também matam a cobra
- [ ] Comidas especiais (douradas, que valem mais pontos ou dão efeitos temporários)
- [ ] Modo dificuldade (fácil / médio / difícil) alterando velocidade e obstáculos
- [ ] Animação suave de movimento (em vez de "pulos" de bloco em bloco)
- [ ] Efeito visual quando a cobra come (partículas, brilho)

### Mais avançadas
- [ ] Modo dois jogadores (duas cobras no mesmo mapa)
- [ ] Cobra controlada por IA (bot) para comparar performance
- [ ] Editor de mapas simples (posicionar obstáculos antes de jogar)
- [ ] Sistema de fases/níveis com objetivos diferentes
- [ ] Ranking local com nomes dos jogadores (tipo os scores do ping pong)
- [ ] Versão web (usando algo como `pygbag` para rodar pygame no navegador)

Vá marcando aqui o que for implementando, assim dá pra acompanhar o progresso do projeto.