# Etapa 114 — transição de clipes, mão na corrida e pulo com a perna da frente

Só `app/src/main/java/com/vinicius/meular/CuteChar.kt` mudou.

## 1. Braço/mão esticando ao entrar/sair da corrida
Causa: a troca de clipe (0,25 s) e o fechamento do punho (rampa de ~0,6 s até 0,9999) interpolavam as matrizes 3x4 dos ossos
linearmente. Com giros grandes, a matriz encolhe/estica e a malha deforma (dedos viravam "espinhos").
- `blendPoses`: rotação por slerp + posição das juntas por cinemática direta (comprimento dos ossos preservado).
  As juntas de repouso saem dos próprios clipes (`restJoints`, mínimos quadrados: junta = ponto fixo comum a osso e pai).
- `blendFingerToWrist`: slerp em torno da junta do dedo (antes o pivô era a origem do modelo).
- `slotFist` agora encosta no alvo (antes levava ~0,6 s só para chegar a 0,9999).
Verificado offline (numpy) com os clipes reais de af5/am5: antebraço no meio da mistura 25,9 cm -> 27,8 cm (= comprimento real);
mão a 30/60% de fechamento sem dedos esticados.

## 2. Pulo correndo com a perna que está à frente
O clipe RUNJUMP sempre sai com a direita. Agora, ao entrar no pulo correndo, compara-se a pose das pernas (ossos 17..24) no último
quadro da corrida com o quadro 0 do clipe original e com o clipe espelhado (M' = S·M·S, ossos esquerdo/direito trocados);
usa o mais próximo. Espelhamento validado: corrida espelhada == corrida deslocada meio ciclo.
Pulo parado (clipe JUMP) não mudou.

## Limite
Sem Gradle/Kotlin aqui: o código Kotlin não foi compilado; a matemática foi testada em Python com os mesmos dados. Teste no aparelho.
