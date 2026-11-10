# Etapa 162 — Tesla Model S branco (veículo do jogador)

- **Modelo**: `app/src/main/assets/obj3d/veic_tesla.glb`, gerado de `ferramentas/tesla/tesla_branco.glb` por `ferramentas/tesla/tesla_para_jogo.py`
  (`python3 tesla_para_jogo.py tesla_branco.glb veic_tesla.glb`; `prev.py` renderiza uma prévia com portas abertas).
  Nós: `corpo`, `dir_FE/FD` (esterço, giram em Y) com `roda_FE/FD` dentro, `roda_TE/TD`, `porta_FE/FD/TE/TD` (dobradiça na quina da frente).
  F = frente, T = trás, E = esquerda (+X, lado do motorista), D = direita. 12 nós, ~5,2 mil vértices, textura 512×512 embutida.
- **Interior** acrescentado (caixas e um torus): bancos, painel, console, volante, tela. O modelo original não tinha interior.
- **`TeslaCar.kt`** (novo): estado das animações. Porta mais perto do jogador abre (até 66°), fecha ao dirigir; giro das rodas = velocidade / 0,355 m;
  cabeceio (±1,4°) e rolagem (±2,2°) suaves.
- **`Renderer3D`**: `ensureCar` carrega o GLB (se falhar, sedã branco no lugar), `drawTesla` monta a pose e desenha; vidros vão para o fim do quadro (`carGlassQ`).
  Tamanho para colisão 2,5 × 1,05 m (meio comprimento × meia largura); entre-eixos 2,96 m; vmax 50 m/s, aceleração 10,5.
- **Loja (Garagem)**: "Tesla Model S" com miniatura; com ele escolhido a pintura é só "Branco".
- Gerador antigo do GLB (cores) não foi mexido; só o branco entra no jogo.
- **Não compilado nem testado no aparelho** (sem Kotlin/Android aqui). O GLB foi lido e validado em Python como o `Glb.kt` lê (índices, materiais, nós)
  e a pose foi conferida numa prévia por software. Pontos a olhar no celular: sentido de abertura das portas, vidros escuros, rodas sem tremer, altura do carro no chão.
