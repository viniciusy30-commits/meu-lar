# Etapa 180 (v6) - Cidade realista: rede de ruas refeita do zero

Por que refiz: a versao anterior tinha rua sem saida, circulo em todo cruzamento e muita rua se cruzando.

- Hierarquia: 1 rodovia elevada (leste-oeste), 8 rotatorias grandes, avenidas que LIGAM os bairros e os centros, e ruas de quadra que saem das avenidas em T (cruzamento reto, sem angulo estranho).
- ZERO ruas sem saida (so as pontas da rodovia/avenidas que saem do mapa).
- Todas as ruas formam uma rede unica conectada (387 trechos, ~210 cruzamentos).
- Bairros: Centro, Parque das Flores, Vila Esperanca, Oeste Alto, Alto da Colina, Bairro Norte, Morro Alto, Jardim Central, Recanto do Sul, Distrito Leste, Porto, Beira-Rio. Morros e rio ficam com natureza (sem rua demais).
- Cruzamentos: Relevo.kt - a placa do cruzamento agora e so um pouco maior que a rua (antes tinha "bolha" redonda).
- 17 casas colocadas, de frente para a rua, em terreno plano.
- Verificado antes de entregar (renderizei o mapa inteiro e os 4 cantos, e rodei auditoria): 0 pontas soltas, 0 ruas se sobrepondo, 1 cruzamento levemente agudo, inclinacao maxima de rua 13% (so nos morros).
- ferramentas/gerador-cidade/: o gerador completo (para nao perder de novo).

Arquivos do app: Relevo.kt, assets/hds/city3.json, assets/hds/relevo.bin.
