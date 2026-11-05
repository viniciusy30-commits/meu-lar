# Biblioteca de objetos 3D (Etapa 83 em diante)

Gera os modelos 3D originais do Meu Lar como **GLB (glTF 2.0)** de verdade, com peças separadas, pivôs, colisores,
pontos de interação e metadados de física/animação em `extras`. O jogo lê esses arquivos direto (`Glb.kt`).

| Arquivo | O que faz |
|---|---|
| `textures.py` | Texturas procedurais (potência de 2) em `tex/` |
| `geom.py` | Primitivas de modelagem (caixa com chanfro, torno, tubo, esfera, disco, vivo de almofada) |
| `glb_lib.py` | Modelo com nós/pivôs, gravação GLB, limpeza (faces invertidas e degeneradas), leitor e **verificador** |
| `ao_core.py` | Sombra de contato (oclusão ambiente) assada na cor dos vértices |
| `pm_lib.py` | Base do Plano Mestre v4: materiais, metadados, loft, extrusão, colocação com encaixe (EMB = 0,5 mm) |
| `conteudo.py` | Conteúdo interno detalhado (roupas, cabides, calçados, comida, embalagens, produtos de limpeza) — nada de cubo/esfera genérica |
| `etapa1.py` | Etapa 1: cadeira, mesa, guarda-roupa — `python3 etapa1.py <saída>` |
| `etapa2.py` | Etapa 2: cama, sofá, geladeira, fogão, pia — `python3 etapa2.py <saída>` |
| `integridade.py` | Regra 1 (v4): separa as peças, mede o vão até o apoio (exato, ponto-triângulo) e reprova qualquer peça solta; portas/gavetas fechadas e abertas |
| `zoom.py` | Prévia ampliada de uma região (conferir o conteúdo interno) |
| `relatorio_v4.json` | Resultado do verificador + integridade (tabela de apoios peça por peça) dos 8 GLB atuais |
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
python3 etapa1.py ../../app/src/main/assets/obj3d && python3 etapa2.py ../../app/src/main/assets/obj3d && python3 integridade.py ../../app/src/main/assets/obj3d/*.glb
python3 thumbs.py ../../app/src/main/assets/obj3d ../../app/src/main/assets/obj3d/thumb
python3 fichas.py ../../app/src/main/assets/obj3d catalogo
```
Testes na JVM (precisa de kotlinc): compile `stubs/**/*.java` com javac, depois
`kotlinc -cp <stubs> Glb.kt Physics.kt Stubs.kt Test.kt -include-runtime -d t.jar` e `java -cp t.jar:<stubs> com.vinicius.meular.TestKt`
(o caminho dos assets está no início de `Test.kt`).
