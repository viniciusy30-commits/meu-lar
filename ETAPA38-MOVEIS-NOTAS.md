# Etapa 38 — móveis do pack home-set-2020s (aguardando teste no celular)

Pedido: adicionar os móveis do unitypackage `home-set-2020s` exatamente como são no pack (sem recriar em código).

## O que mudou
- `ferramentas/moveis/buildmob.py` (+ `mobparse.py`, `mkspec.py`, `mobspec.json`, `mobview.py`): lê os FBX e os materiais do Unity (cor, textura, tiling) e gera `assets/mob/<id>.bin` (formato MOB1), `assets/mob/tex/*` (texturas em potência de 2, até 1024) e `assets/mob/icons/<id>.png` (miniaturas da loja).
- Tamanho real em metros, sem escala: a pegada em casas é o tamanho do modelo arredondado para cima (tolerância de 10 cm). Sofá de canto 5x3, sofá baixo 5x3, tapetes longos 5x2, escrivaninha 3x2, aparador 3x1.
- `Mob.kt` (`MobLoader`): lê MOB1, sobe as texturas (REPEAT, mipmap) e devolve a `Mesh`. `Models.furniture` usa isso quando `Type.mob != null`.
- `GameState.kt`: `Type` ganhou `mob` e `rug`; 49 entradas `MOB_*` no fim (as antigas e os saves não mudam). Tapetes/mousepad usam `rug` (pisáveis, sem sombra), no lugar da checagem `Type.RUG`.
- `Gfx.kt`/`Renderer3D.kt`: `Part.cut` + `uCut` no shader (folhas da planta recortadas pelo alfa); `fm.clear()` e `MobLoader.reset()` quando o contexto GL é recriado.
- `MainActivity.kt`: a loja mostra a miniatura do móvel (campo `thumb` em `Entry`).

## Fora (de propósito)
- Paredes, portas, janelas, cortinas, quadros e fotos de parede (11 paredes, 3 portas, 3 janelas, 3 cortinas, 3 quadros, 4 fotos, 1 pôster): o app já faz paredes/portas/janelas por código e não tem como pendurar objeto na parede.
- Mapas de normal e de rugosidade do pack não são usados (o shader do app só usa a cor).

## Limites
- Sem compilador de Android aqui: o build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.
- Objetos pequenos (livros, mouse, patinho...) ficam no chão, em tamanho real, em 1x1 casa.
- Texturas do pack são pequenas (a maioria 256 a 512 px).
