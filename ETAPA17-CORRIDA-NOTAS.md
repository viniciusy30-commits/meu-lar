# Etapa 17 — nova animação de correr (Running.fbx) — aguardando teste no celular

Pedido: colocar a nova animação de correr e tirar a antiga.

## O que mudou
- `assets/cute/base.bin`: o clipe **RUN (índice 3)** foi trocado pelo `Running.fbx` (Mixamo), adaptado ao esqueleto de 55 ossos com o mesmo retargeting da Etapa 11. A corrida antiga (Slow_Run) saiu. O clipe 6 (corrida masculina da Etapa 14, sem uso porque `MALE_CLIPS = false`) também foi trocado pela nova, para não sobrar nenhuma corrida antiga no arquivo.
- **Parado, Andar, Pulo e clipes 4-5 ficaram idênticos** (conferido quadro a quadro), e a malha/pesos não foram tocados.
- `Renderer3D.kt`: `RUN_SPEED` 2,45 → **2,05** m/s, a velocidade natural do clipe novo (medida pelo recuo do pé de apoio: 2,02 a 2,12 m/s). Sem isso o pé deslizaria.
- `ferramentas/anim/Running.fbx` + `ferramentas/etapa17_corrida.py` (troca só a corrida; reproduzível).

## Clipe novo
| clipe | duração | quadros | velocidade natural |
|---|---|---|---|
| Correr | 0,833 s (1 ciclo = 2 passos) | 51 (60 fps) | ≈ 2,05 m/s |

O ciclo é um pouco mais lento e mais ereto que o antigo (0,733 s, 2,45 m/s).

## Verificações feitas aqui
- Matrizes de pele ortonormais (erro 4e-15), sem NaN, laço fecha exato (primeiro = último quadro).
- Pé mais baixo toca y = 0; mediana do pé de apoio ≈ 0,5 cm acima do chão.
- Renderização de 8 quadros de lado, antes x depois (`previa-corrida.png`): passada, braços dobrados e inclinação do tronco corretos.
- O `Running.fbx` não tem deslocamento embutido (é "no lugar"), por isso a velocidade foi medida pelo pé.
- Sem compilador/aparelho aqui: o build do GitHub é a prova final.

## Para ajustar
- Pé deslizando ao correr: mude `RUN_SPEED` em Renderer3D.kt (menor se o pé "patina" para trás, maior se parece arrastar).
- Arquivo antigo `ferramentas/anim/Slow_Run.fbx` não é mais usado pelo jogo; pode apagar do repositório (o zip não consegue apagar arquivos).
