# Etapa 108 — Correção visual das roupas masculinas (camiseta, short, jeans Minimalist)

## Causas encontradas (medidas) e correções
| Problema | Causa | Correção |
|---|---|---|
| Buracos, "orelhas" nos ombros, mangas e barras serrilhadas | usava o LOD1 e apagava todo triângulo com 1 vértice em área transparente | `Ts4Cloth`: usa o LOD0 e remove só triângulos cuja maioria dos pontos amostrados é transparente |
| Jeans "capri" (20 cm acima, ~11% menor) | busca automática de escala/posição (`Fit.place`) caiu num mínimo errado | escala fixa `s0` do corpo; jeans agora vai de y≈9 a y≈108,9 (original 8,7–108,8) |
| Pele atravessando joelhos, quadris, ombros | empurrão por vértice, ruidoso e de uma passada só | campo de deslocamento suave (vértices soldados nas costuras de UV) em várias passadas, medindo também centros e pontos médios de aresta |
| Barra em "boca de sino" / mangas em asa | refinamento empurrando extremidades | barra de short/calça só na 1ª passada; camiseta com teto de 1,1 no refinamento |
| Linhas escuras em cinturas/barras, textura baixa | atlas 2048x4096 reduzido com média incluindo fundo preto | textura recortada na região usada, borda preenchida (bleed), potência de 2 até 1024 |
| Cunhas de pele sumidas abaixo da barra | `Cover.markSurface` tratava a quina da borda aberta como "coberta" | ignora ponto cujo vetor corre ao longo do tecido (não por baixo dele) |

## Arquivos
- NOVO `mods/Ts4Cloth.java`, `mods/T3Geo.java`; ALTERADO `mods/Cover.java`, `ferramentas/mods_teste/T3.java` (main usa o `Ts4Cloth`).
- Assets regenerados: `assets/cute/skate/minimalist_{top,short,jeans}_am5.{cup,png}` (o workflow `minimalist-convert.yml` gera os mesmos a partir do T3.java).
- `ferramentas/render_roupas/render_roupas.py`: renderizador (numpy) frente/costas/perfil. Uso: `python render_roupas.py pasta_saida`.
- `imagens-roupas-ts4/`: antes_* e depois_* (+ comparações).

## Medido
- Triângulos de pele ocultos abaixo da barra do jeans: 63 → 31; acima da cintura: 39 → 14 (short 33 → 14).
- Pontos de roupa (vértices+centros) dentro do corpo: camiseta 10/2036, short 25/1030, jeans 17/1574 (medida aproximada pelos 4 vértices de corpo mais próximos; inspeção visual sem furos).

## NÃO validado (sem Gradle/Android aqui)
- Compilação do app (Kotlin não alterado; só Java do importador compilou aqui com JDK 21).
- Caminhada e corrida: não renderizei poses; os pesos de osso continuam copiados do corpo mais próximo.
- Só a 1ª cor de cada pacote (18/12/11 cores existem). Dentro do jogo (iluminação/máscara de mãos e pés) só o teste no celular confirma.
