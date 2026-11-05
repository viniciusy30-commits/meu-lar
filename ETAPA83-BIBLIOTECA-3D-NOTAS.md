# Etapa 83 — Biblioteca 3D, Etapa 1 (protótipo)

## Criado
- 5 GLB originais em `app/src/main/assets/obj3d/` (vaso com costela-de-adão, caixa de papelão, bola, poltrona, aparador) + miniaturas.
- `Glb.kt`: leitor de GLB (nós, pivôs, malhas, materiais, texturas embutidas, extras).
- `Physics.kt`: corpos rígidos (caixa/esfera) com gravidade, atrito, quique, contatos com piso/paredes/móveis/objetos/personagem e sono.
- Renderer3D: desenho dos GLB por peça, animação de portas/gavetas/almofada, teste de parede/móvel antes de abrir, portas abertas
  bloqueiam o personagem, física dos objetos soltos, interação (Sentar/Levantar/Abrir/Fechar) e a sequência de sentar com cancelamento.
- CuteChar: clipes 5 Sentar, 6 Sentado, 7 Levantar (Universal Animation Library, `ferramentas/etapa83_sentar.py`); os 5 clipes antigos
  ficaram idênticos byte a byte. `cute/sit.txt` = altura do assento de cada corpo.
- GameState: tipos `G_*`, estado gravado por item (pose da física, peças abertas).

## Testado aqui (sem celular)
- Verificador de GLB: 5/5 sem erros nem avisos.
- Glb.kt e Physics.kt compilados com kotlinc e executados na JVM (stubs do Android): os 5 GLB lidos; 9 cenários de física aprovados.
- Renderer3D/CuteChar/GameState/Foot/Models compilados junto com o projeto: nenhum erro no código novo (só referências ao SDK do
  Android, que não existe aqui). MainActivity não foi compilado (depende do androidx).
- Pose sentada do corpo real sobre a poltrona renderizada: assento e encosto sem atravessar.

## Não testado (só no aparelho)
Desenho no GL, interação na tela, câmera sentado, desempenho, gravação/reabertura.
