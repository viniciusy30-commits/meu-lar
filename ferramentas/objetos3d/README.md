# Biblioteca de objetos 3D (Etapa 83 em diante)

Gera os modelos 3D originais do Meu Lar como **GLB (glTF 2.0)** de verdade, com peças separadas, pivôs, colisores,
pontos de interação e metadados de física/animação em `extras`. O jogo lê esses arquivos direto (`Glb.kt`).

| Arquivo | O que faz |
|---|---|
| `textures.py` | Texturas procedurais (potência de 2) em `tex/` |
| `geom.py` | Primitivas de modelagem (caixa com chanfro, torno, tubo, esfera, disco, vivo de almofada) |
| `glb_lib.py` | Modelo com nós/pivôs, gravação GLB, limpeza (faces invertidas e degeneradas), leitor e **verificador** |
| `ao_core.py` | Sombra de contato (oclusão ambiente) assada na cor dos vértices |
| `models.py` | Os objetos (uma função por asset) — `python3 models.py <saída>` grava e verifica cada GLB |
| `preview.py` | Renderiza o GLB relido do disco (com portas/gavetas em qualquer posição) |
| `thumbs.py` | Miniaturas da loja a partir dos GLB |
| `fichas.py` | Ficha técnica (Plano Mestre v3) de cada asset + `manifesto.json` |
| `catalogo/` | Fichas por categoria, manifesto e relatório do verificador |
| `testes_jvm/` | Teste do leitor GLB e da física com o código Kotlin real (Glb.kt, Physics.kt) na JVM, com stubs do Android |

Convenção: metros, Y para cima, frente +Z, origem no centro do piso do objeto. Nós `COL_*` (colisores), `IP_*` (pontos de
interação: posição da raiz do personagem e para onde ele olha), `SURF_*` (superfícies de apoio). Peça móvel = nó com
`extras.anim` (`dobradica` / `trilho` / `escala`, eixo, min, max, dur, alça).

Para refazer tudo:
```
python3 textures.py
python3 models.py ../../app/src/main/assets/obj3d
python3 thumbs.py ../../app/src/main/assets/obj3d ../../app/src/main/assets/obj3d/thumb
python3 fichas.py ../../app/src/main/assets/obj3d catalogo
```
Testes na JVM (precisa de kotlinc): compile `stubs/**/*.java` com javac, depois
`kotlinc -cp <stubs> Glb.kt Physics.kt Stubs.kt Test.kt -include-runtime -d t.jar` e `java -cp t.jar:<stubs> com.vinicius.meular.TestKt`
(o caminho dos assets está no início de `Test.kt`).
