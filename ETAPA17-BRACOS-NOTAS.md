# Etapa 17 — braços do masculino (aguardando teste no celular)

Pedido: a pose dos braços do masculino parecia feminina (abertos para fora). Depois: 8° ficou colado demais; queria mais separado, mas com postura masculina.

## Causa
A pose parada (Idle) vem "assada" no `base.bin`: braço ~26° aberto, antebraço curvado para fora (mãos ~7-8 cm além do quadril). Masculino e feminino usam o mesmo clipe.

## O que mudou (só `CuteChar.kt`, só masculino)
- `MALE_ARM_IN = 4f`: graus que o braço inteiro gira para o corpo, em torno do ombro.
- `MALE_FOREARM_IN = 6f`: graus extras só do antebraço+mão, em torno do cotovelo (cotovelo afastado, antebraço mais vertical, mão perto da coxa).
- Aplicado nas matrizes de osso depois da animação (Idle e Andar 100%, Correr 50%, Pulo 0%), com transição suave. Feminino não muda.

## Conferência
Simulação em Python com as matrizes reais do base.bin: mão fica em x≈14-18 cm (quadril ≈13), ou seja, 1 a 5 cm de folga. Sem compilador aqui: o build do GitHub é a prova final.

## Ajuste (topo de CuteChar.kt)
Mais separado: baixe `MALE_ARM_IN` (ex. 2) ou `MALE_FOREARM_IN`. Mais junto: suba. Original = 0 e 0.
