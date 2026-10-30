# PLANO-VIVO — personagem fofinho (meu-lar)

Objetivo (não muda): customização de personagem bonita, fofinha e bem feita; sem polígonos estranhos.

## Passos
- [x] 1. Primitivas lisas novas: Cute.kt (MB.ell = elipsoide com rotação; MB.limb = cápsula cônica)
- [x] 2. AvatarModel.build refeito: cabeça grande, olhos em camadas com brilho, bochechas, boca, cílios, orelhas, tronco/braços/pernas arredondados, 9 cabelos, 4 barbas, 4 óculos (lente translúcida), 5 roupas
- [x] 3. Câmera do criador ajustada ao novo tamanho (Creator.kt)
- [x] 4. novidades.txt
- [x] 5. REVISÃO feita (rodada 2): conferidos tipos/assinaturas de ell/limb/lathe/cyl, usos externos de AvatarModel (só Renderer3D: build/stage, inalterados) e escala na casa (altura 1,47, ok). Sem compilador local; build do GitHub é a prova final
- [x] 6. Polimento: dispensado (visual já completo; evitar risco de build sem compilador)

## Decisões
- Mantido o formato salvo do Avatar (encode/decode) para não quebrar saves.
- Sem mudar shader/Renderer; suavidade vem de elipsoides com normais corretas e mais segmentos.

## Arquivos alterados
app/src/main/java/com/vinicius/meular/{Cute.kt (novo), Avatar.kt, Creator.kt}, app/src/main/assets/novidades.txt

## PRÓXIMO PASSO
Nenhum. Missão concluída; se o build falhar, corrigir só o erro apontado.
