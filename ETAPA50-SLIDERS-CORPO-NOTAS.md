# Etapa 50 - Sliders de corpo (corpo do Sims 3)

Pedido: "Coloque os sliders de corpo pra deixar o jogo ainda mais completo" (referencia: Slider Master Files do Sims 3).

## O que mudou
- Aba **Corpo** do criador agora tem **27 sliders** (-100% a +100%, com ima no zero), em 6 grupos:
  Geral (Altura, Peso, Cabeca), Tronco (Ombros largura/altura, Peito, Cintura, Barriga, Postura, Torso comprimento),
  Busto (tamanho, altura, distancia), Quadril e pernas (Quadril, Bumbum, Coxas, Vao das coxas, Panturrilhas, Tornozelos, Pernas comprimento),
  Bracos e maos (espessura, antebracos, comprimento, Maos), Pescoco e pes (espessura, comprimento, Pes). Botao "Zerar tudo".
- Valem para todos os corpos do Sims 3 (bebe ate idoso, magro/normal/gordo, feminino/masculino) e a roupa de baixo e o cabelo acompanham o corpo.
- As animacoes (Idle/Andar/Correr/Pulo) nao mudaram; o pe continua no chao (a altura da camera/lift ja se ajusta).

## Como funciona
- `assets/cute/bodyrig.txt`: 23 pontos do esqueleto de cada corpo (ombro, cotovelo, punho, quadril, joelho, tornozelo, alturas do peito/pescoco...), gerado por `ferramentas/etapa50_rig_sliders.py`.
- `BodyMorph.warpSim` (Kotlin) deforma as posicoes de repouso de todas as pecas; portado de `ferramentas/etapa50_sliders_ref.py` (que tambem desenha a conferencia: cinza = original, vermelho = +100, azul = -100).
- `CuteChar`: carrega o bodyrig, escolhe a tabela pelo corpo em uso (ex.: `body/S_af1` -> `af1`) e usa `warpSim` no lugar da deformacao antiga.
- Save: os 10 sliders antigos ficam no lugar de sempre; os 17 novos vao no fim do texto salvo. Saves antigos abrem com tudo em 0 (igual a antes).

## O que testar no celular
1. Base > Corpo: mexer em cada slider e ver a mudanca na hora (nada de buracos ou pontas); soltar e reabrir o app mantem os valores.
2. Trocar idade/sexo/tipo de corpo: os sliders continuam valendo e o corpo nao "quebra".
3. Extremos (+100/-100) de Busto, Postura e Pernas: se algum ficar feio, avisar qual para ajustar o ganho.
4. Sem compilador aqui: o build do GitHub e a prova final.
