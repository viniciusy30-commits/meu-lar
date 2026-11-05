# Etapa 89 – Desempenho, protótipos de volta e interação sem animação

## Desempenho
- **Dois programas de shader** (`Renderer3D.buildProg/useProg`): opaco sem `discard` e recorte com `discard` (folhas, cabelo, cartões).
  Com `discard` no único shader, as GPUs de celular (Mali/Adreno, renderização por blocos) perdem o teste de profundidade antecipado em
  TODOS os desenhos e pintam cada pixel escondido. Os uniformes do quadro (olho, sala, luz) ficam guardados e são reaplicados na troca.
- **Precisão média** no fragment shader (antes `highp`, bem mais caro nas GPUs Mali).
- **Resolução dinâmica** (`MainActivity.ajustarResolucao`): o 3D é desenhado com o lado menor em ~720 px (antes: resolução nativa com
  MSAA 4x) e a escala se ajusta a cada 1,2 s: abaixo de 45 FPS desce 15% (mínimo ~380 px), acima de 58 FPS sobe 8% (máximo 900 px).
- **Recorte por câmera**: móveis fora do campo de visão não são desenhados (`boxVisible`).
- `GModel.ips` com cache (a mira chamava a lista a cada quadro).
- **Contador de FPS** opcional (Configurações), para medir no aparelho.

## Protótipos de volta (revisados pela v4) — `ferramentas/objetos3d/etapa0.py`
- Poltrona (pés agora nascem verticais sobre a sapata: estavam 1,6 mm abaixo do piso; caixa `alvo` para a mira), aparador (portas e
  gavetas embutidas com dobradiça de pino e corrediças — antes as prateleiras e a tigela flutuavam e as gavetas soltavam ao abrir),
  vaso (pedrinhas assentadas na terra), caixa e bola (física). Todos aprovados no `integridade.py`.
- Conteúdo do aparador (só desenhado com porta/gaveta aberta): pilhas de pratos com friso, tigelas, xícaras com pires, toalhas de mesa,
  organizador de talheres (garfos, facas, colheres) e guardanapos; castiçais com velas no tampo.

## Interação
- `USE_ANIM = false`: interagir não toca mais o clipe 8 (braço esticado); a peça muda na hora. Lavar as mãos abre a torneira, espera e fecha, sem levantar a mão.

## Não testado no aparelho
