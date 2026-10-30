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

## PRÓXIMO PASSO
Se o build falhar, corrigir só o erro apontado. Se passar: ver o personagem no celular e ajustar rosto/moicano/desempenho conforme o que aparecer.
