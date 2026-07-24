# Jogo da Cobrinha (Snake)

Versão simples do clássico jogo da cobrinha, feita em Python com [pygame](https://www.pygame.org/).

## Como rodar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
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
- **1 Jogador / Jogador vs Bot**: setas ou `WASD` controlam o jogador
- **2 Jogadores**: Jogador 1 usa `WASD`, Jogador 2 usa as setas
- **Editor de Mapa**: setas movem o cursor, `Espaço`/`Enter` alterna obstáculo, `C` limpa tudo, `S` salva e sai, `ESC` cancela
- **Ranking**: `Enter` ou `ESC` para voltar ao menu; ao bater uma pontuação alta, digite o nome e pressione `Enter`

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
- Modo de jogo (Configurações → Modo): **1 Jogador**, **2 Jogadores** (local, mesmo mapa) ou **Jogador vs Bot**
- No modo 2 Jogadores, colisão frontal entre as duas cobras (ou uma encostar na outra) mata a(s) envolvida(s); vence quem tiver mais pontos ao final
- `escolher_direcao_bot()` é a IA do bot: evita paredes/obstáculos/corpos e persegue a comida pela distância mais curta
- `tela_editor_mapa()` permite desenhar um layout de obstáculos próprio, salvo em `mapa_personalizado.txt` — ativado em Configurações → Mapa: Personalizado
- Sistema de fases: a cada `PONTOS_POR_FASE` pontos a fase sobe e novos obstáculos aparecem no mapa (até um teto), com um aviso "Fase X!" na tela
- `tela_ranking()` e `tela_entrada_nome()` implementam um ranking local (top 10) salvo em `ranking.json`; ao terminar uma partida (fora do modo 2 Jogadores) com pontuação boa o suficiente, o jogo pede um nome
- O jogo inteiro roda em cima de `asyncio` (loop principal e todas as telas são `async def` com `await asyncio.sleep(0)` a cada quadro), preparado para rodar no navegador via [pygbag](https://github.com/pygame-web/pygbag) — veja a seção "Versão web" abaixo

## Versão web (experimental, via pygbag)

O código já está estruturado de forma compatível com [pygbag](https://github.com/pygame-web/pygbag), que empacota jogos pygame para rodar no navegador (WebAssembly), sem precisar reescrever a lógica do jogo.

Para testar localmente:
```bash
pip install pygbag
python -m pygbag cobrinha.py
```
Isso sobe um servidor local (normalmente em `http://localhost:8000`) servindo o jogo rodando no navegador.

Observações importantes:
- Arquivos como `recorde.txt`, `config.txt`, `ranking.json` e `mapa_personalizado.txt` são gravados no sistema de arquivos virtual do navegador; a persistência entre sessões depende da configuração de armazenamento do pygbag (IndexedDB) e pode exigir ajustes extras para funcionar de forma confiável.
- Som e desempenho no navegador podem variar entre navegadores/dispositivos.
- Essa é uma primeira adaptação; o ideal é testar em um navegador real antes de considerar "pronta para produção".

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

### Mais avançadas (implementadas)
- [x] Modo dois jogadores (duas cobras no mesmo mapa)
- [x] Cobra controlada por IA (bot) para comparar performance
- [x] Editor de mapas simples (posicionar obstáculos antes de jogar)
- [x] Sistema de fases/níveis com objetivos diferentes (mais obstáculos a cada fase)
- [x] Ranking local com nomes dos jogadores
- [x] Base para versão web com `pygbag` (loop assíncrono já implementado — veja "Versão web" acima)

Todas as melhorias sugeridas inicialmente já foram implementadas! Novas ideias podem entrar aqui conforme forem surgindo.