# Etapa 181 - Ruas: cruzamentos e rotatorias sem bug
- Fim dos discos nos cruzamentos: as pistas vao inteiras ate o centro; o meio-fio ganha "bocas" onde outra rua se abre; a faixa central some dentro do cruzamento.
- Rotatorias: a pista comeca dentro do circulo (sem cunha de grama) e o anel abre exatamente na largura de cada pista (inclusive elevadas).
- Curvas entre pistas: as duas pontas usam a mesma normal (sem quina aberta).
- Pontas niveladas nos cruzamentos, com rampa maxima mantida (13,1%; antes do ajuste chegava a 24,6%).
- Casas nas mesmas posicoes. Dados novos: city3.json, relevo.bin. Gerador: ferramentas/gerador-cidade/gen_city7.py.
- Nao compilado aqui: o build do GitHub e a prova. Se falhar, corrigir so o erro apontado.
