# Etapa 115 — tênis Dunk High: pé atravessando e perna bugada

Causas (renderizadas offline com o corpo am5, o CUP do tênis e os clipes reais):
1. O jogo escondia a pele sob o tênis por proximidade (`Cover.mark`, 284 triângulos): sobrava pé furando a sola e a biqueira.
2. A máscara gravada no CUP1 (570 triângulos) usava os ossos 18/22 — que são a PANTURRILHA, não o tornozelo — e apagaria a canela até o joelho (e as miniaturas mostravam isso). Além disso, o jogo aplicava essa máscara ao corpo-base, não ao corpo do Sims.

Correção:
- `dunk_high_am5.cup`: máscara regravada por altura: todo triângulo do corpo am5 abaixo de (topo do cano − 4,5 cm) = 306 triângulos. A canela fica inteira e entra no cano do tênis.
- `CuteChar.kt`: sapato com máscara própria agora esconde exatamente esses triângulos no corpo do Sims (am5); a máscara do sapato não é mais aplicada ao corpo-base.
- Render antes/depois: `imagens-etapa115/sapato-antes-depois.png` (parado e correndo).

Limites: só o Dunk High (am5) tem máscara própria; outros sapatos seguem o método antigo. Sem Gradle aqui: Kotlin não compilado.
Inclui também a Etapa 114 (CuteChar.kt já contém as duas).
