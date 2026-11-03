# Etapa 43 — Julie (Sims 3, MTS whiterider Bodies/Faces/Skins) — aguardando teste

- Personagens prontos > "Julie". Corpo `afBody_fit` + rosto `afface` + couro cabeludo `afscalp` do Sims 3, peça única `body/Julie`, ligada ao esqueleto do app (pesos copiados do base.bin por vizinho mais próximo; cabeça = osso 8). Pernas, braços e ombros ajustados às juntas do app.
- Olhos esféricos castanhos nos buracos do rosto; sobrancelhas e delineado suave pintados; top branco e short jeans pintados na pele; descalça.
- Cabelo: Heartbeat (já no app) reajustado à cabeça dela: `hairBack/HeartbeatJulie`.
- Pele do corpo: `tfBody.dds` (feminino adolescente) com o tom igualado ao do rosto, porque `afBody.dds` veio corrompido no RAR.
- Enquanto a Julie está ativa, roupas, cabelos e ajustes de corpo/rosto do criador não se aplicam. Para sair: Masculino ou Feminino (Corpo ou Base).
- Limitações: rosto não pisca nem muda de expressão; cor da pele fixa.
- `Avatar.kt`: campo `julie` no fim do texto salvo (saves antigos continuam válidos). `CuteChar.kt`: slot "body" gerenciado. `pieces.txt`: 2 linhas novas.
- Gerador: `python3 ferramentas/etapa43_julie.py <pasta com bodies/ faces/ skins/> app/src/main/assets/cute` (precisa de base.bin, heartbeat.png e p_hairback_heartbeat.bin nessa pasta).
- Sem compilador local: o build do GitHub é a prova final.
