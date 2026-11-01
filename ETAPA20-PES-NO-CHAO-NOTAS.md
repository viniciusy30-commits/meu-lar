# Etapa 20 — Sola dos sapatos apoiada no chão (aguardando teste no celular)

Problema: a parte de baixo dos sapatos (All Star, chinelo, botas...) ficava dentro do piso e não aparecia.

Causa (medida nos .bin): o corpo-base apoia em y=0, mas a sola dos sapatos desce abaixo disso e o jogo nunca compensava.
No parado: All Star ≈1,9 cm, chinelo/sandália ≈1,0 cm, tênis 1,0–1,5 cm, botas ≈2,9 cm abaixo do chão (no andar/pulo/corrida é menos, e varia por clip).

Correção (só código, nenhum asset mudou):
- `CuteChar.kt`: `updateLift/computeLift/lift(slot)`. Para cada clip mede o ponto mais baixo (corpo-base + sapato "feet/...") em todos os quadros,
  já com a altura do personagem (`heightS`), e guarda o valor por clip (recalcula se a roupa ou as proporções mudam). A subida é suavizada entre clips (~0,1 s).
  Só olha vértices de repouso com y < 8 (sola/calcanhar/biqueira); conferido no PC que dá o mesmo resultado que olhar todos.
- `Renderer3D.kt`: `drawPlayer`, `drawCreator` e `drawHouseAvatar` somam `CuteChar.lift(slot)` ao y do personagem (só quando é o personagem novo, não o reserva).
- Folga de 1,5 mm para a sola não brigar com o piso (z-fighting). Sem sapato, o pé do corpo-base também é considerado.

Valores esperados (cm de subida, parado/andar/pulo/correr): All Star 2,0/1,3/1,7/1,4 · sandália e chinelo 1,2/0,5/0,9/0,6 · botas de trabalho 3,0/2,2/2,8/2,2.

Para testar: ver All Star, chinelo e bota no criador, andando e parado na casa — a sola deve aparecer inteira em cima do piso, sem flutuar.
Se achar que "flutua" no andar, é o ponto mais fundo do clip; dá para trocar `low` em `computeLift` por um valor médio. Sem compilador aqui: o build do GitHub é a prova final.
