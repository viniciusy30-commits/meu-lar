# Etapa 11 — animações de andar e correr do Mixamo (aguardando teste no celular)

## O que mudou
- `assets/cute/base.bin`: os clipes **WALK** (índice 1) e **RUN** (índice 3) foram trocados pelas animações enviadas (`Walking.fbx` e `Slow_Run.fbx`, Mixamo), adaptadas ao esqueleto de 55 ossos. **Idle e Jump ficaram idênticos** (conferido byte a byte), e a malha/pesos não foram tocados.
- `CuteChar.kt`: `WALK_RATE` 1,2 → **0,96** (o clipe de andar natural anda a 1,335 m/s; × 0,96 = 1,28 m/s, a velocidade que o jogo já usava).
- `Renderer3D.kt`: `RUN_SPEED` 2,6 → **2,45** m/s (velocidade natural do clipe de corrida, medida).
- O resto não mudou: analógico ≥ 88% corre (volta a andar abaixo de 70%), botão verde, blend de 0,25 s entre andar/correr.
- `ferramentas/anim/`: os dois FBX originais. `ferramentas/etapa11_*.py`: a conversão (reproduzível).

## Clipes novos
| clipe | duração | quadros | velocidade natural |
|---|---|---|---|
| Andar | 0,967 s (1 ciclo = 2 passos) | 59 (60 fps) | 1,335 m/s |
| Correr | 0,733 s (1 ciclo = 2 passos) | 45 (60 fps) | 2,45 m/s |

Primeiro e último quadro são idênticos (laço fecha sem salto).

## Como foi feito (retargeting)
O Mixamo está em T-pose com 65 ossos; o personagem está em A-pose com 55 ossos e proporções diferentes. Não havia o esqueleto de referência no repositório (`game_skel.pkl` dos scripts antigos), então ele foi **reconstruído dos próprios clipes do base.bin** (cada osso filho é um ponto fixo do osso pai em todos os quadros; resíduo ≈ 0).
- Pelve, coluna (5 ossos ← 3 do Mixamo, interpolados), pescoço, cabeça e clavículas: rotação mundial do Mixamo relativa à T-pose.
- Coxa, canela, pé, braço, antebraço: a **direção** do osso no mundo é igualada à do Mixamo (isso resolve T-pose × A-pose e proporções diferentes).
- Mão e dedão do pé: rotação relativa ao osso pai, transferida. Dedos das mãos: relaxados como no Idle.
- Raiz: o deslocamento para frente foi removido (o jogo move o personagem); mantém quique e balanço de quadril. Escala pelo comprimento da perna (0,96).
- Trava de chão: o ponto mais baixo do pé em todo o ciclo toca y = 0.

## Verificações feitas aqui
- Matrizes de pele ortonormais (erro 2e-7, det = 1), sem NaN, laço exato.
- **Deslize do pé** (centro da sola enquanto o pé está plano): andar recua a 1,34 m/s (esperado 1,32); correr 2,44 m/s (esperado 2,46) → ≈ 1% de erro.
- Pé de apoio fica rente ao chão (mediana ≈ 0,5 cm acima).
- Renderização de silhuetas (lado e frente) de ambos os clipes: passada, braços, inclinação do tronco e simetria corretas.

## Limites
- Sem compilador/aparelho aqui: o build do GitHub é a prova final (só mudou 1 arquivo binário e 2 constantes).
- Cabelo longo e roupas largas não têm física: acompanham o corpo rígido (como antes).
- Roupas muito largas podem atravessar um pouco as pernas/braços em passadas grandes.
- A rotação em torno do eixo do osso (torção) de coxa/braço não é transferida (só a direção); não aparece nas silhuetas, mas pode mudar sutilmente o caimento de mangas.

## Para ajustar
- Andar mais rápido/lento: mude `WALK_RATE` (CuteChar.kt) **e** a velocidade `1.28f` (Renderer3D.kt) juntos: `1,28 = 1,335 × WALK_RATE`.
- Correr mais rápido/lento: `RUN_SPEED` em Renderer3D.kt (o pé desliza se mudar sem ajustar o clipe).
- Regerar: `cd ferramentas && python3 etapa11_retarget.py <base.bin antigo> anim/Walking.fbx anim/Slow_Run.fbx <base.bin novo>` (precisa de numpy; o base.bin de entrada precisa ter os 4 clipes).
