# DECISOES - Cidade 5 (Meular City)

## Fatos confirmados no repositorio
- `Relevo.kt` le `hds/*.json` com `roads[]` (c: 0/1 avenida/rodovia, 2 coletora, 3 local; w largura; `p` = x,z,y,ponte a cada 4 numeros, somando CX=CZ=300), `rounds[]` (x,z,r,y,arms), `houses[]`, `bld/lamp/hyd/tree` e `relevo.bin` (nx, nz, passo, alturas cm).
- `UserMap.kt` limita o mundo a 1000x800 m (NX=126, NZ=101, G=8). A Cidade 5 usa 2700x2100 m: o formato de saida (Etapa I) precisa ler `world` do JSON (ja le) e `nx,nz` do `.bin` (ja le); o limite so existe no editor.
- Casas do Hds: caixas em `city2.json` -> `plots`. A orientacao real da frente ainda NAO foi confirmada (Etapa D).

## Decisoes
- Mundo 2700x2100 m; grade mestra e perfis exatamente como na especificacao. Tudo em `plan.py`.
- Contorno irregular (PARTE 3.4b): `CITY_MASK` com 60+ vertices, entalhe a oeste (serra), entalhe ao norte, enseada da marina (com Ponte da Marina), baia a sudeste, cabo a sudoeste e Peninsula Real separada (so por ponte). Vias urbanas cortadas pela mascara terminam em cul-de-sac (raio 12 m); infraestrutura (rodovia, marginais, pontes, extensoes a leste da Av. Leste) e isenta.
- Rotatorias: 7 da especificacao + a da Peninsula (2560,1752) = 8 (a tabela 3.4 so listava 7).
- Alcas da rodovia: 4 alcas de 8 m de largura (declive 6,25 % limite do validador 6,5 %).
- Hospital: quarteiroes (1,1),(2,1),(1,2),(2,2) da SQ(3,0) fundidos (ruas internas removidas).
- Condominio Rio Azul (SQ(4,2)): rua central + 2 transversais (privadas).
- Arena (SQ(4,0)): uma coletora E-O em Z=394. Marina (SQ(1,3)): coletora N-S em X=902.

## Pendencias / duvidas para as proximas etapas
- Etapa A so gera o GRAFO de ruas (JSON proprio `city5_roads.json`) e a previa. A conversao para o formato `Relevo.kt` (polilinhas com y/ponte, normais de emenda, `cl/cr`) e a Etapa I.
- Calcada/guia/faixas (Etapa C) e terreno (Etapa B) ainda nao existem; o app nao carrega a Cidade 5 ainda.
- Nada foi testado em aparelho.
