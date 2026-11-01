# Etapa 18 — pescoço que descolava + nova animação de pulo (aguardando teste no celular)

## 1. Pescoço "descolando" ao se mover
**Causa.** O pescoço do `base.bin` é feito de 3 malhas soltas (tronco, faixa do pescoço, cabeça) que se encontram em anéis de
vértices na *mesma posição*, mas com pesos de osso diferentes (tronco: `spine_04`; cabeça: `head`). Quando a cabeça gira em relação ao tronco,
os dois lados do anel se afastam e aparece um degrau/fresta. Medido nos clipes (pares de vértices coincidentes):

| clipe | antes | depois |
|---|---|---|
| Parado | 0,65 cm | 0,01 cm |
| Andar | 1,41 cm | 0,01 cm |
| Pulo (antigo) | 0,74 cm | 0,01 cm |
| Correr | **7,30 cm** | 0,01 cm |

**Correção (só pesos de osso; posições, UVs, normais e animações não mudam).**
1. Solda: vértices na mesma posição passam a ter exatamente os mesmos pesos (valem os do tronco > pescoço > cabeça): 173 grupos acertados.
2. Degradê: na coluna do pescoço (y 140–157) os pesos viram função só da altura, passando suavemente por
   `spine_05 → neck_01 → neck_02 → head` (o `neck_02` quase não era usado). A mesma função vale para blusas/vestidos/barbas
   (`top`, `overall`, `beard`), então a gola e a barba acompanham a pele.

Arquivos: `base.bin` + as peças `p_top_*`, `p_overall_*`, `p_beard_*` que chegam ao pescoço. Cabelo, calças, sapatos etc. não mudaram.
Script reproduzível: `ferramentas/etapa18_pescoco.py <cute entrada> <cute saída>` (precisa de numpy e scipy).

## 2. Animação de pulo (Jumping.fbx, Mixamo)
- Clipe **JUMP (índice 2)** do `base.bin` trocado, com o mesmo retargeting da Etapa 11. Parado, Andar, Correr e clipes 4–6 ficaram **idênticos** (conferido).
- O arquivo dura 2,37 s (agacha → voa → amortece → levanta). No jogo a altura vem da física (`vy = 3,9`, `g = 11` → **0,709 s no ar**) e o pulo já começa no ar,
  então foi usada só a fase aérea (0,867 s a 1,45 s do FBX), esticada para 0,709 s (44 quadros a 60 fps). Termina com os joelhos dobrando para a aterrissagem;
  ao tocar o chão o jogo já mistura (0,25 s) para parado/andar.
- Para a altura não somar duas vezes (física + Mixamo), a pelve é re-travada a cada quadro (ponto mais baixo do pé em y = 0).
- Nenhum arquivo `.kt` mudou: o clipe novo tem a mesma duração do voo (0,709 s), que é o que `Renderer3D` usa.
- Conferência: matrizes de osso ortonormais (erro 1e-7), sem NaN; clipe visto de lado em 8 quadros.
- Script: `ferramentas/etapa18_pulo.py <base.bin> anim/Jumping.fbx <saída>`; FBX em `ferramentas/anim/Jumping.fbx`.

## Limites / o que testar
- Sem compilador/aparelho aqui: o build do GitHub é a prova final (só mudaram arquivos binários).
- Testar: andar e correr olhando o pescoço (de lado e de frente), com e sem gola alta (TurtleNeck/Hoodie), com barba; pular parado e andando.
- O pulo não tem a fase de agachar antes de sair do chão (o jogo decola no mesmo instante do toque). Se quiser, dá para adicionar um pequeno atraso de decolagem.
- Para outra janela do pulo: `JANELA_A/JANELA_B` no topo de `etapa18_pulo.py`.
