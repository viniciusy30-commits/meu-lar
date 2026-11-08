# Etapa 113 — animações dos braços masculinos e correção do polegar

## Objetivo
Fazer o modelo masculino adulto do The Sims 4 (`am5`) usar os mesmos movimentos de braços, ombros, punhos e dedos do modelo feminino (`af5`) em todas as animações, sem substituir a passada masculina. Corrigir também o polegar de ambas as mãos durante a corrida.

## Alterações

### 1. Retarget dos braços masculinos
- `clips_am5.bin` foi regenerado a partir dos clipes masculinos existentes e dos movimentos locais dos braços do `clips_af5.bin`.
- Ossos transferidos: clavículas, braços superiores, antebraços, mãos e 30 ossos dos dedos (38 ossos no total).
- A rotação local feminina é aplicada à hierarquia masculina; as posições das juntas são recalculadas com os comprimentos do rig masculino.
- Tronco, cabeça e pernas continuam usando os movimentos masculinos originais. Portanto, a passada e a postura do corpo masculino não foram substituídas.
- A alteração cobre os 11 clipes: parado, andar, pulo, correr, pulo correndo, sentar, levantar, interação e agachamentos.

Ferramenta reprodutível: `ferramentas/etapa113_bracos_femininos_masculino.py`.

### 2. Polegar e transição do punho
- `CuteChar.kt` agora usa pivôs de dedos separados para `af5` e `am5`, obtidos do esqueleto TS4 de cada corpo.
- O pivô do polegar também usa a profundidade correta de cada rig; antes, os dois corpos usavam o mesmo ponto, apesar de as mãos terem posições diferentes.
- O tuck do polegar foi reduzido de 35° para 18°. A flexão é específica por corpo: `af5 = (-22°, 25°, 35°)` e `am5 = (-30°, 25°, 35°)`, porque a mão masculina é mais larga e precisa de um pequeno afastamento adicional. O polegar fica apoiado por cima dos dedos sem atravessar o indicador.
- A mistura da mão com a pose do punho agora interpola a rotação por quaternion (slerp) e a translação separadamente. A interpolação linear anterior deformava a matriz 3×3 e encolhia/esticava a mão durante a entrada e saída da corrida.
- O fechamento continua restrito à corrida e ao pulo correndo; andar, parado e os demais clipes mantêm as mãos soltas.

## Validações executadas
- Os 11 clipes masculinos foram gerados e reabertos como `CLP1` válido (55 ossos por quadro).
- Rotações locais dos 38 ossos de braço/mão comparadas com as femininas: erro máximo entre `7e-9` e `1.11e-7`.
- Comprimentos das juntas masculinas preservados: erro máximo observado de 0,038 cm, decorrente do resíduo de interpolação nos quadros de fechamento do ciclo.
- Ossos fora dos braços/mãos permanecem idênticos ao clipe masculino de origem.
- Geração repetida: SHA-256 de `clips_am5.bin` permaneceu idêntico na segunda execução (script idempotente).
- Render offline de todos os 11 clipes dos dois corpos. Comparativos de andar, correr e pulo em `imagens-etapa113/`.
- Render de ambas as mãos na corrida para `af5` e `am5`. A menor distância entre os vértices distais do polegar e do indicador ficou em aproximadamente 1,01 cm no feminino e 1,07 cm no masculino; a distância entre os eixos das juntas permaneceu acima de 1,4 cm nas animações de corrida e pulo correndo.
- Bloco Kotlin de interpolação compilado com `kotlinc`; teste numérico confirmou que a matriz mantém escala uniforme durante o slerp (`QUATERNION_BLEND_OK`).

## Limite do teste
Não foi possível compilar o APK Android neste ambiente: o projeto não contém `gradlew` e não há Gradle/Android SDK instalado. Os renders foram feitos com as malhas e clipes reais do projeto, mas a confirmação final no aparelho depende do build e teste após o envio do ZIP para `_incoming/`.

## Arquivos alterados/adicionados
- `app/src/main/assets/cute/clips_am5.bin`
- `app/src/main/java/com/vinicius/meular/CuteChar.kt`
- `ferramentas/etapa113_bracos_femininos_masculino.py`
- `imagens-etapa113/*.png`
- `ETAPA113-BRACOS-MAOS-NOTAS.md`
- `INCOMING-ETAPA113.md`
- `PLANO-VIVO.md`
