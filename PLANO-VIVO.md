# PLANO-VIVO — personagem fofinho (meu-lar)

Objetivo (não muda): customização de personagem bonita, fofinha e bem feita; sem polígonos estranhos.
Feedback mais recente do usuário: corpo parecia "boneco de feira" (peças coladas), rosto feio, mãos as piores; quer o mais profissional e natural possível.

## Passos
- [x] 1. Cute.kt/AvatarModel (elipsoides) — primeira versão, agora usada só como reserva (Avatar.buildCute)
- [x] 2. Motor de escultura em Java (pacote sculpt): campos de distância (SDF) com união suave + malha por surface nets
  - Prims (elipsoide, cone arredondado, ruído), Mesher, Layer (malha + tags de material por vértice)
  - Body (corpo contínuo, cabeça com maxilar/bochechas/nariz/lábios, mãos com dedos), Eyes
  - Gear (cabelos 1..8, barbas 1..3, camisa/regata/vestido/saia/shorts/calça, sapatos, óculos), Figure (monta tudo, cores, cache, pedaços indexados)
- [x] 3. Integração no app: SculptAvatar.kt (ponte + AvatarBuilder em segundo plano, com ticket), Gfx.Part com índices curtos, Renderer3D com glDrawElements, Avatar.build com reserva caso dê erro
- [x] 4. Câmera do criador (Creator.kt) para o corpo mais alto (≈1,57 m); pinça aceita zoom mais perto (GameView.kt)
- [x] 5. Testes no PC: 156 combinações (gênero × corpo × cabelo/roupa/calça/óculos/barba) sem erro nem NaN; 150–175 mil triângulos, ~1,4 s a frio / ~0,2 s com cache
- [x] 6. novidades.txt

## Decisões
- Formato salvo do Avatar (encode/decode) não mudou: saves antigos continuam valendo.
- Se o motor novo falhar por qualquer motivo (Throwable), cai no modelo antigo de elipsoides.
- Montagem fora da thread de desenho; a thread GL só troca a malha quando ela fica pronta (o personagem anterior continua na tela enquanto isso).
- Shader/iluminação do app não mudaram; lente dos óculos usa alfa por vértice (sem passada de vidro).

## Pontos a olhar com o APK no celular
- Tempo da primeira montagem e FPS (≈85 mil vértices, 145–175 mil triângulos).
- Rosto: estilizado e fofo, mas pode precisar de ajuste fino (nariz pequeno, cabeça meio oval).
- Moicano (cabelo 6): laterais podem parecer carecas demais.

## Arquivos alterados
app/src/main/java/com/vinicius/meular/{SculptAvatar.kt (novo), sculpt/*.java (novos), Gfx.kt, Renderer3D.kt, Avatar.kt, Creator.kt, GameView.kt}, app/src/main/assets/novidades.txt

## Rodada final (proporções/mãos/rosto)
- [x] Torso mais alto/largo, braços mais finos e curtos, pernas e quadril reajustados; roupas acompanham
- [x] Mãos refeitas (palma, polegar, 4 dedos) e caixa de malha da mão ampliada (pontas dos dedos não são mais cortadas)
- [x] Rosto mais fino estilo Sims (mandíbula, queixo, maçãs do rosto mais altas, lábios mais cheios)
- [x] Teste PC: 324 combinações sem erro/NaN

## PRÓXIMO PASSO
Se o build falhar, corrigir só o erro apontado. Se passar: ver o personagem no celular e ajustar rosto/moicano/desempenho conforme o que aparecer.

## Pack Cute Characters (importação de teste)
- [x] Pack (RAR5, unitypackage armazenado) extraído: 25 personagens (f_1–f_12, m_1–m_13), 7 animações, textura 128–1024, material
- [x] f_1.fbx (binário) convertido por script Python (fora do app) para assets/cute/f_1.bin: malha 6550 vértices / 8986 triângulos, 64 ossos, pesos (4 por vértice), animações Idle e Walk em matrizes por quadro (24 fps), altura normalizada 1,5 m, frente em +Z
- [x] CuteChar.kt: carrega o .bin, pele na CPU por quadro, textura própria (Part.tex); Renderer3D usa no criador (Idle) e na casa (Idle/Walk); se falhar, volta ao personagem antigo
- [ ] Ainda NÃO compilado/testado no celular (sem Gradle no ambiente). Se o build falhar, corrigir só o erro apontado
- [ ] Próximo: peças modulares (cabelo/roupa separáveis) e importar mais personagens; painel antigo de personalização REMOVIDO (Creator.kt só tem o botão Pronto)

## Câmera 3ª pessoa + pulo
- [x] Renderer3D: `third` (padrão ligado), câmera orbitando o personagem (2,7 m, encurta dentro da casa), drawPlayer (Walk/Idle, vira para a direção do movimento), sombra, pulo (py/vy, jumpReq)
- [x] Ui.kt: ícones CAMERA e JUMP; MainActivity: botão de câmera no topo, botão de pular (só no modo andar)
- [ ] Não compilado nem testado no celular. Pular não passa por cima de móveis (colisão é só no plano)

- [x] Animação de pulo: clip Jump = primeiros 17 quadros do "Song Jump" do pack (assado no f_1.bin, 3º clip); drawPlayer usa jumpT (tempo no ar) para sincronizar

## Rodada Mary (BoZo Stylized Modular Characters)
- [x] Extraído o unitypackage do RAR e lidos os FBX (leitor próprio); montada a Mary: corpo, cabeça, olhos, suéter, saia, sandálias, cabelo traseiro (Flare) e franja (LongSweeps) = 14.691 vértices, 24.062 triângulos, 55 ossos (com dedos)
- [x] Textura única 2048x1024 (assada das máscaras do pack com as cores da Mary.asset); mesmo formato CUT1 lido por CuteChar.kt (arquivos cute/f_1.bin e cute/textures.png, nomes mantidos; CuteChar.kt não mudou)
- [x] Animações criadas à mão nos ossos: Idle 3 s (laço), Walk 1 s (laço), Jump 0,71 s (sem agachar; o jogo já começa no ar)
- Limitações: cabelo e olhos presos à cabeça (sem física); mãos com dedos abertos como no modelo original; saia segue as coxas
- Licença: o pack veio de site de redistribuição; para publicar o jogo, ter a licença original do BoZo
## Rodada animação do andar (Mary)
- [x] Walk refeito: ciclo de 0,8 s (passada ±25°, joelho até ~57°), braços relaxados (balanço ±21°, cotovelo ~26–50°), contra-rotação de pelve/coluna/cabeça, altura da pelve ajustada por quadro para o pé de apoio tocar o chão (ground-lock); coxa não atravessa mais a saia
- [x] CuteChar.kt otimizado: os 55 ossos são interpolados uma vez por quadro (antes por vértice, ~4x mais caro) — causa provável das travadinhas
- [x] CuteChar.frame(clip, t, slot): fase do laço reinicia ao trocar de clip e transição suave de ~0,15 s (0,06 s para o pulo); slots 0 = jogador, 1 = avatar da casa, 2 = criador (Renderer3D passa slot nas chamadas 1 e 2)
- [ ] Ainda não compilado nem testado no celular
- Ferramentas de geração (fora do repo): scripts Python em /home/claude (fbx.py, ext.py, asm.py, anim.py, build.py, render.py); a animação é gerada em anim.py (walk/idle/jump) e assada em f_1.bin
## PRÓXIMO PASSO
Ver no APK: se o andar ainda parecer rápido/lento demais, ajustar só o comprimento do ciclo (0,8 s em build.py) e a amplitude S em anim.py; mãos ainda ficam com dedos abertos (possível curvar dedos).
