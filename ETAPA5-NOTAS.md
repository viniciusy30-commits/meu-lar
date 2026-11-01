# Etapa 5 — sapatos, luvas, chapéus, óculos, barbas e acessórios de cabeça (aguardando teste no celular)

## O que entrou
- 31 peças novas (CUP1) do pack BoZo: 11 sapatos/botas (+ a sandália da Mary), 3 luvas, 5 chapéus, 4 óculos, 6 barbas, chifres e antenas.
- Atlas novo `cute/extra2.png` (+ `extra2_recolor.png`, `extra2_recolor_s.png`, `extra2_recolor.txt`): terceira camada de cor em `CuteColor.kt`.
  Regiões: 1 = barba (slots Cabelo/Pontas), 4 = sapatos (slots Sandália/Tiras), 5 = acessórios e 6 = lentes escuras (slots novos Acessório/Acessório 2).
- Slots de cor 10 e 11 ("Acessório", "Acessório 2"): `CuteColor.SLOTS` passou de 10 para 12.
- Save: `Avatar.encode` ganhou 8 números no fim (cores 11 e 12, sapatos, luvas, chapéu, óculos, barba, cabeça). Saves antigos continuam lendo (ficam com a sandália da Mary e sem acessórios).
- Criador (`Creator.kt`): partes novas "Sapatos", "Luvas", "Chapéu", "Óculos", "Barba", "Cabeça".
- `CuteChar.MANAGED` inclui feet, gloves, hat, glasses, beard e headAcc.
- Regra: com chapéu a franja (hairFront) não é desenhada. O cabelo de trás continua.

## Como as peças foram feitas
- Sapatos, luvas e barbas têm esqueleto no FBX: pesos dos clusters. Ossos sem equivalente no jogo: `Jaw` e olhos -> cabeça (osso 8); `calf_twist_01_l1/r1` -> canela.
- Chapéus, óculos, chifres e antenas não têm esqueleto: ficam no espaço local da cabeça (mesma convenção dos cabelos, deslocamento HEAD) com 100% no osso da cabeça.
- Óculos não têm textura no pack: usam tile sólido recolorível (óculos escuros usam a região 6, que começa escura).
- Ferramenta: `ferramentas/etapa5_extra.py` (precisa de `fbxr.py`, `clothes_lib.py`, `idx.pkl` e o pack aberto).

## Ocultação do corpo (feita sobre o main com biquíni)
- `ferramentas/etapa5_ocultar.py`: esconde os triângulos do pé (sapatos) e da mão/dedos (luvas) cobertos pela peça, como na Etapa 4 (distância 1,5 e normal alinhada). Já aplicada nos .bin.
- Botas grandes cobrem pouco pelo critério (poucos triângulos); o pé fica dentro da bota, então não deve aparecer. Se aparecer pele atravessando, aumentar a distância no script.
- Sem compilador aqui: o build do GitHub é a prova final.

## O que testar no celular
1. Cada sapato/bota: pé encaixado, sem flutuar, andando e pulando.
2. Luvas: acompanham a mão e os dedos.
3. Chapéus: assentados na cabeça; ver se o cabelo de trás atravessa a copa.
4. Óculos no rosto, barbas na mandíbula (se descolarem ao andar, ajustar pesos).
5. Cores: "Sandália/Tiras" nos sapatos; "Acessório/Acessório 2" em luvas, chapéus, óculos, chifres e antenas; barba segue "Cabelo/Pontas".
