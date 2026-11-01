# Etapa 21 — Pele não aparece mais através das roupas (aguardando teste no celular)

Problema: nas roupas (calças, blusas, vestidos...) a pele aparecia por baixo do tecido e piscava ao mexer, às vezes até parado.

Medido nos .bin (poses parado/andar/correr): a maioria dos triângulos de pele ainda visíveis perto da roupa tem o tecido por cima, mas a folga é de poucos mm
(e pele "furando" o tecido aparece mais na corrida). Como a pele e a roupa são desenhadas juntas, a profundidade empata e fica piscando.

Correção (só código, nenhum asset mudou):
- `Gfx.kt`: `Part.push` (metros), empurrão na profundidade, padrão 0.
- `Renderer3D.kt`: shader de vértice com `uPush` (recua a peça ao longo da visão); `draw` envia `p.push` por peça.
- `CuteChar.kt`: o corpo-base (pele) usa `SKIN_PUSH = 0.007` (7 mm). A roupa, cabelo, sapatos etc. ficam em 0, então o tecido sempre ganha da pele.

Efeito colateral possível: onde a pele está a menos de 7 mm na frente de uma roupa (ex.: braço colado no tronco) a borda pode ficar escondida.
Se acontecer, baixar `SKIN_PUSH` (ex.: 0.004); se ainda aparecer pele, subir (0.010).
Sem compilador aqui: o build do GitHub é a prova final.
