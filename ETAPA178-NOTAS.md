# Etapa 178 - Cidade com relevo (sem grade)
- Novo mapa 3200 x 2400 m: morros, rio, lago, mar, ruas curvas (83), 11 rotatorias, pontes e arvores. As 17 casas (com interior) ficam longe umas das outras, sobre platos do terreno.
- Dados: assets/hds/relevo.bin (alturas a cada 8 m) e assets/hds/city3.json. Sem esses arquivos o jogo continua com a Cidade 2 antiga.
- Gerador corrigido: ruas se encontram com no maximo ~1 m de degrau (antes 2,45 m); rampa maxima 15% (antes 27%); terreno nao fura mais o asfalto (pior caso 0,45 m, antes 2,88 m).
- Relevo.kt (novo): terreno, agua, ruas, rotatorias, pontes e arvores; o jogador anda sobre o asfalto, inclusive pontes e rotatorias; agua funda bloqueia; a rua sobe onde o terreno encostaria nela.
- Hds.kt: casas nas posicoes do mapa novo, subindo/descendo para o plato (pisos, escadas, porao e colisoes acompanham).
- City.kt / Renderer3D.kt / CityMap.kt: terreno desenhado ate ~420 m, camera 3a pessoa e vista de cima seguem a altura do chao, nasce na Casa 1 na altura certa, limite de voo na borda sul, mapa com agua/morros/ruas/lotes e mais zoom.
- Tesla: agora nasce na rua em frente da Casa 1 (Relevo.carSpot), na altura do asfalto. Em morros o carro nao e mais tratado como "em cima do elevado": da para descer dele e ele colide com casas/agua.
- Nao compilado aqui (sem compilador): o build do GitHub e a prova. Se falhar, corrigir so o erro apontado.
