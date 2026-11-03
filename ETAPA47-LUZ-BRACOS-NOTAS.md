# Etapa 47 — Luz na pele e braços mais naturais (aguardando teste)

Prints do criador mostraram faixa branca com borda dura em ombros, pescoço, peito e testa.
Causa: no criador há uma luz pontual a 2,1 m de altura; nas superfícies voltadas para cima o shader somava quase 2x de luz e a pele estourava para branco.
- Shader (`Renderer3D.kt`): novo `uSoft`; só nas peças de pele (`Part.soft`, `Gfx.kt`, ligado em `CuteChar.kt`) a soma de luz é limitada mantendo a cor. O resto do jogo não muda.
- Animações (`clips_*.bin`): o braço inteiro gira em torno do ombro, para perto do corpo (parado/andar 8–9°, correr 5°; pulo igual). Ajuste em `ADD_DEG` (`ferramentas/etapa45_rig.py`).
- Continua valendo a Etapa 46 (pele um pouco mais escura).
- Sem compilador local: o build do GitHub é a prova final.
