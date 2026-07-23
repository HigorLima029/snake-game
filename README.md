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

## Como está estruturado hoje

- `gerar_comida()` sorteia uma posição livre no grid para a comida
- `rodar_jogo()` contém o loop principal: entrada do usuário, movimento, colisões e desenho
- `tela_de_fim()` mostra a pontuação final e pergunta se quer jogar de novo
- Sem sons, sem menu inicial, sem níveis — só o essencial pra já ficar jogável

## Ideias de melhorias

- [ ] Tela de menu inicial (Jogar / Sair)
- [ ] Guardar e mostrar recorde (high score) em um arquivo local
- [ ] Aumentar a velocidade gradualmente conforme a pontuação sobe
- [ ] Sons de efeito (comer, colidir) com `pygame.mixer`
- [ ] Pausar o jogo com `ESC` ou `P`
- [ ] Cores/skins diferentes para a cobra (escolher tema)

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
