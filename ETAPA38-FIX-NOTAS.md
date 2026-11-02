# Etapa 38 - fix5

Corrige o erro de build `Mob.kt: Unclosed comment` (comentario de bloco aninhado em `mob/tex/*`).

- `app/src/main/java/com/vinicius/meular/Mob.kt`: cabecalho e comentarios trocados de bloco para `//`. Codigo inalterado.
- Este arquivo existe so para o zip ter mais de um item na raiz (zip com uma unica pasta na raiz estava sendo extraido sem a pasta `app/`, caindo em `src/` na raiz do repo).
