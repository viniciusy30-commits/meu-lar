# Etapa 87 – Plano Mestre v4: limpeza, Etapa 1 corrigida e Etapa 2

## 1. Móveis anteriores ao PDF retirados do jogo
- Saíram do enum `Type` (loja, sala de testes, casa inicial): os 14 móveis do pacote antigo (cadeira, mesa, cama, sofá, estante, planta,
  tapete, TV, geladeira, fogão, abajur, criado-mudo, mesa de centro, guarda-roupa), poltrona, aparador, vaso, caixa de papelão, bola,
  painel de cerca, poste, banco de jardim e caixa de correio. Arquivos `flora/f_*.bin`, `bench/mailbox/lamp_post/gate_lantern.bin` e os GLB/miniaturas apagados.
- Quintal: sem postes, banco, caixa de correio, lanternas do portão e vasos da varanda. Ficaram plantas, árvores, canteiros, cerca-viva, cerca do lote e caminho.
- Saves antigos: itens que não existem mais são ignorados ao carregar (já era assim). Casa nova: cama de casal, mesa de jantar e 2 cadeiras.
- Sala de testes: dentro só os móveis do PDF; todas as plantas e árvores (cat 4) do lado de fora (`Models.yard(..., vitrine = true)`): árvores à esquerda da casa, arbustos/flores à direita.

## 2. Regra 1 (nada flutuando) — `ferramentas/objetos3d/integridade.py`
Separa cada GLB em peças (componentes conexos da malha), mede a distância exata entre superfícies (pontos a cada 1,5 mm nas arestas de
uma peça contra os triângulos da outra, nos dois sentidos) e exige que toda peça chegue ao piso por contatos de até 2 mm. Roda com
portas/gavetas fechadas e abertas. Resultado (todos aprovados, tabela de apoios em `ferramentas/objetos3d/relatorio_v4.json`):

| GLB | peças | soltas (fechado/aberto) | vértices | triângulos |
|---|---|---|---|---|
| int_cadeira_jantar | 24 | 0 / 0 | 1 588 | 2 084 |
| int_mesa_jantar | 22 | 0 | 1 862 | 2 476 |
| int_guarda_roupa | 750 | 0 / 0 | 53 579 | 67 180 |
| int_cama_casal | 70 | 0 | 12 617 | 18 374 |
| int_sofa3 | 29 | 0 | 8 004 | 12 592 |
| int_geladeira | 450 | 0 / 0 | 33 032 | 41 278 |
| int_fogao | 208 | 0 / 0 | 12 271 | 14 362 |
| int_pia | 107 | 0 / 0 | 10 635 | 12 862 |

Falhas reais que o verificador achou e foram corrigidas: cantoneiras da mesa soltas, pés da cadeira 1,7 mm abaixo do piso,
cabideiro e caixa organizadora do guarda-roupa flutuando, porta do guarda-roupa atravessando as laterais, botões da cabeceira, vivos e listras soltos.

## 3. Regra 2 (conteúdo interno detalhado) — `ferramentas/objetos3d/conteudo.py`
Guarda-roupa: cabides (gancho de arame encostado no tubo, braços de madeira, barra), 5 camisas (gola, carcela com botões, bolso, mangas com punho, uma xadrez) e vestido (corpete, faixa, saia com pregas e estampa), jeans (bolso com pesponto, cós, passadores, rebite), camisetas (mangas dobradas, gola canelada, estampa), suéteres (tranças, punhos), toalhas (dobras, barra listrada), caixa organizadora (tampa, pegadores, etiqueta), tênis (sola, biqueira, cabedal, língua, ilhoses, cadarço, laço), sapatilha (salto, debrum, laço), meias enroladas (punho canelado) e roupa íntima (elástico) nas gavetas.
Geladeira: garrafas (gargalo, anel, tampa estriada, rótulo), caixas de leite (telhado, aba, tampa), porta-ovos com ovos, maçã (covinha, cabo, folha), laranja (poros, umbigo), tomate (gomos, sépalas), penca de banana, cenoura (rama), alface (camadas de folhas), potes com tampa e comida, queijo em cunha (casca, furos) no pratinho, frios na bandeja, manteigueira, iogurtes, latas (anel de abrir), bisnagas (tampa flip); freezer com formas de gelo (cubos no vidro), saco de congelados (soldas serrilhadas) e pote de sorvete.
Fogão: grade do forno nas guias e bolo na forma. Pia: sifão, detergentes, borrifador, esponjas, pano de prato e lixeira de pedal.
Android: o conteúdo fica em nós com `extras.mostrar_quando` e só é desenhado com a porta/gaveta correspondente aberta (`GModel.showWhen`).

## 4. Etapa 2 (fichas do PDF)
- **Cama**: postes, laterais, peseira, estrado (sarrafos, viga com 2 pés, 15 ripas), colchão com vivo e respiros, lençol, edredom com espessura (3 cm, cai pelos lados e pelo pé sem atravessar o colchão), dobra do lençol, 2 travesseiros e 2 almofadas, cabeceira estofada com capitonê. COL_base (bloqueia) e COL_colchao separado (não bloqueia), sem colisor na roupa de cama. Lados E/D com ocupação por lado; aproximar → alinhar → sentar na borda → deitar → **Dormir** → **Acordar** → sentar → levantar. O sono fica salvo (`sono=<lado>` no estado do item) e o personagem volta dormindo ao abrir o jogo.
- **Sofá**: 6 pés, braços contínuos com vivo, base, encosto com traseira modelada (costuras), 3 almofadas de assento separadas (vivo, volume variado) e 3 de encosto apoiadas no assento e encostadas na estrutura. 3 pontos de sentar com ocupação por lugar; a almofada do lugar afunda.
- **Geladeira**: pés niveladores, base com grade, caixa com espessura, 4 prateleiras de vidro sobre nervuras, gaveta de legumes (trilho, só abre com a porta aberta), 3 nichos na porta, vedação de borracha, puxadores, dobradiças com pino (em cima, no meio, embaixo), luz interna que acende com a porta. Portas com limite de 110° e teste de parede.
- **Fogão**: pés, base, laterais, fundo, forno esmaltado com guias, porta com moldura inox, **vidro duplo** e puxador (dobradiça embaixo), mesa, encosto traseiro, 4 queimadores (copo, espalhador com fendas, tampa), 2 grades de ferro com pés de borracha, panela com tampa e alças. **5 botões, cada um no seu eixo**: cada boca acende só a própria chama; o do forno acende a resistência. Estado *cozinhando* = boca da panela acesa (sai vapor). As chamas ficam abaixo da grade e do fundo da panela.
- **Pia**: rodapé, gabinete, tampo de pedra em volta da cuba, espelho, cuba inox com borda apoiada, fundo com caimento e ralo com cesto, cano + sifão em U até a parede, torneira com bica alta e arejador, alavanca que gira, água que cai no ralo, 2 portas. **Lavar as mãos** (IP_lavar): vai até a frente da cuba, vira, abre a torneira com a animação de interagir, deixa a água correr 3,5 s e fecha.

## 5. Código do jogo
- `GameState.kt`: enum só com plantas + itens do PDF; casa inicial; `Item.occ` (ocupação por lugar) e `Item.sleep` (gravado como `sono=`); sala de testes sem cat 4 dentro.
- `Glb.kt`: `showWhen` (conteúdo interno), efeito `vapor`, `slotVerbs` (Acender/Apagar, Ligar/Desligar, Abrir/Fechar torneira).
- `Renderer3D.kt`: peças de vidro dos GLB e água/vapor desenhados no fim (translúcidos); ocupação por lugar; fase 10 = dormindo; ação 8 (Dormir/Acordar) e 9 (Lavar); restaurar o sono; rótulos com os verbos da peça.
- `Models.kt`: móveis antigos removidos; quintal sem os objetos antigos; vitrine de plantas na sala de testes.

## 6. O que NÃO foi testado / limitações
- Nada foi testado no aparelho. Compilado só contra stubs: sem erro novo em GameState/Glb/Renderer3D/Models (o único aviso novo é `JSONArray.optString`, que falta no stub, não no Android).
- A geladeira não tem inventário de alimentos (a ficha diz "opcional"). Lavar as mãos usa o clipe de interagir para abrir/fechar a torneira e fica parado enquanto a água corre: a biblioteca de animações não tem um clipe de esfregar as mãos.
- A escolha da boca do fogão é pela posição do personagem (o botão mais perto); é preciso dar um passo para o lado para trocar de boca.
- O guarda-roupa tem 53 mil vértices; o conteúdo só é desenhado com a porta aberta, mas vale medir o FPS com as duas portas abertas.
