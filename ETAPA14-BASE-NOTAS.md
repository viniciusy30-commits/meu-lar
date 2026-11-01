# Etapa 14 — base masculina/feminina do zero (aguardando teste no celular)

Pedido: a Mary era a base de tudo, então qualquer personagem herdava feições e poses femininas.

## O que mudou
- `Avatar`: padrões novos sem roupa da Mary (cabelo Chanel+franja de lado; sem blusa/calça/sapato). `applyBase(masc)` recomeça do zero mantendo pele e olhos. Base masculina não usa a faixa de sutiã.
- `Creator`: categoria "Base" (Masculino/Feminino) é a primeira; abre nela.
- `BodyMorph`: deformação masculina bem mais forte (ombros, peito, peitoral, deltoide, trapézio, braços, cintura reta, quadril/coxa finos, glúteo reto, pescoço). Conferida: Kotlin e `ferramentas/etapa14_corpo.py` dão números idênticos.
- `CuteChar`: rosto masculino com Masculinidade 100%, sobrancelha +40%, cílios -60%; no masculino usa os clipes 4 (parado), 5 (andar), 6 (correr).
- `base.bin`: +3 clipes masculinos gerados por `ferramentas/etapa14_clips.py` (pés afastados, peito aberto, braços relaxados, dedos curvados). Clipes 0-3 (feminino) intactos.

## Limites
- Textura do rosto (lábios rosados) é igual para os dois; não mexi.
- Sem aparelho: o build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.
- Se o masculino ficar forte/fraco demais, os números estão no topo de `BodyMorph.kt` (M_*).
