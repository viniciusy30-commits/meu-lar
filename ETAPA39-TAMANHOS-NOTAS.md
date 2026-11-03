# Etapa 39 - tamanho dos móveis e física (aguardando teste no celular)

Pedido: todos os itens de decoração do tamanho certo em relação ao personagem; a física dos itens seguir o tamanho real (não a casa inteira).

## O que mudou
- `Foot.kt` (novo): lê o tamanho real de cada móvel (pegada no chão + altura) da própria malha e aplica a escala dos móveis do pack. Escala para a proporção do personagem (~1,75 m): sofás 0,72-0,75, poltrona 0,85, mesas de centro 0,7, cadeira de escritório 0,7, escrivaninha 0,8, planta grande 0,7, tapetes longos 0,6, monitor 0,7, luminária articulada 0,6, almofadas 0,6, etc. Peças pequenas ficam como estavam (já eram do tamanho de verdade). Para mudar, é só editar `ESC` em `Foot.kt`.
- `Mob.kt`: `MobLoader.bounds(id)` lê os limites do `.bin` sem usar o GL.
- `GameState.kt`: `Item` ganhou `ox/oz` (deslocamento fino em metros). `canPlace` compara os corpos reais (giro incluído). `placeAt` encosta o móvel na parede. `rotate` gira em volta do centro. `findPlaceNear` acha lugar de 25 em 25 cm. O save guarda `ox/oz` em centímetros no fim de cada item (saves antigos carregam normal).
- `GameView.kt` / `Renderer3D.kt`: arrastar (vista aérea) e segurar (1ª pessoa) andam de 25 em 25 cm. O personagem bate no corpo real do móvel (+24 cm de folga). Coisas com menos de 12 cm de altura (teclado, mouse, bandeja...) dá para pisar por cima. Toque/seleção usa a caixa real. Sombra e anel de seleção têm o tamanho real do móvel.
- `Models.kt`: `shadowF` e `ringF`. `MainActivity.kt`: comprar usa `findPlaceNear`.

## Limites
- Sem compilador aqui: o build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.
- Os móveis não empilham (livro em cima da mesa ainda não): dois móveis não ocupam o mesmo lugar.
- A grade de compra no chão do tamanho em casas (ex.: 5x3) continua igual na loja; só a colisão e o desenho usam o tamanho real.
