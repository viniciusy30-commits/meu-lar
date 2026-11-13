# DECISOES - Cidade 5 (Meular City) v2

## Mudanca de direcao (feedback do usuario)
A grade retangular (superquadras) foi descartada: "quadradona, repetitiva, pequena". Codigo antigo guardado em `old_grid/` (nao usado).

## Fatos do repositorio (confirmados)
- `Relevo.kt` le `roads[]` (c: 0/1 avenida/rodovia, 2 coletora, 3 local; w; p = x,z,y,ponte x4; soma CX=CZ=300), `rounds[]`, `houses[]`, relevo em celulas de 8 m. Conversao para esse formato = Etapa I.
- `UserMap.kt` limita o editor a 1000x800 m; a Cidade 5 tem 4400x3600 (o `Relevo.kt` ja le `world`, `nx`, `nz` do arquivo).

## Decisoes da Etapa A v2
- Mundo 4400x3600 m, campos de trabalho de 16 m (o heightmap final de 8 m sai na Etapa B).
- Relevo: montanhas ao redor (ruido fractal + cumes), 9 colinas, bacia urbana com contorno por ruido + 2 enseadas, mar ao sul, 2 estreitos, rio, lagoa.
- Mascara urbana: terra > 0,55 m, < 150 m, declive < 34 %, afastada 1 celula da agua, componentes >= 900 celulas (0,23 km2).
- Rede: campo de tensores (grades zonais, radial na lagoa, alinhamento a agua, curvas de nivel nas colinas) + linhas de fluxo em 3 niveis (ave 360 m, col 150 m, loc 80 m de separacao), planarizacao, fusao de nos (9 m), poda de tocos < 80 m.
- Pontes vermelhas: Z=1500, oeste (290->800) e leste (3640->4100), torres em 330/750 e 3680/4060, tabuleiro +34 m, portais de tunel em (90,1420) e (4310,1440). Estradas de montanha e acessos sao polilinhas provisorias; terraplenagem na Etapa B.
- Anel da Lagoa (ave) com 4 ligacoes; 9 rotatorias; 4 pontes sobre o rio (3 geradas + ligacoes).
- Declive: 1 trecho local a 25 % (limite 16 %): sera resolvido pela terraplenagem/ajuste na Etapa B.

## Pendencias
- O app ainda NAO carrega a Cidade 5. Nada testado em aparelho.
- Zoneamento exato dos bairros/casas/profissoes (Etapa D) e orla/parques (Etapa F).
