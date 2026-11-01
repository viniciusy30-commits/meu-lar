# Etapa 16 — base masculina = John do pack BoZo — aguardando teste

Pedido: a base masculina estava torta/bugada; usar um personagem masculino pronto do pack (John) como base.

## Descoberta
O pack não tem malha de corpo masculina: `Body_BasicBody.fbx` é um corpo só (13 pedaços, sem blendshapes) e as cabeças SharpHead/YoungSharpHead
têm a mesma forma da padrão. Os masculinos (John, 1DefaultMale, Dave...) são configurações em cima desse corpo.
Receita do `John.asset`: rosto BodyType 100; ossos clavícula x1,10 e shoulder_twist x1,12 (ombros mais largos), resto neutro;
visual: QuicklyHair + Buzzed, Henley, LooseJeans, CoolShoes, barba cheia. Mesmas animações do feminino.
(A Etapa 14 deixava inchaço na cintura/quadril e ombros em degrau: valores 2 a 5 vezes maiores.)

## O que mudou
- `BodyMorph.kt`: `M_*` do masculino = John: ombros +0,6, deltoide +0,7, peito/braço +0,15, resto 0; altura x1,0; peitoral, trapézio,
  glúteo e peso lateral extras zerados; `BUST_BASE_M` -1,0.
- `CuteChar.kt`: rosto masculino só com Masculinidade 100% (como o pack); `MALE_CLIPS = false` usa as animações aprovadas do feminino
  (clipes 4-6 seguem no base.bin; `true` volta a usá-los).
- `Avatar.applyBase(true)`: nasce com o visual do John (cabelo Raspado + QuicklyHair, Henley, LooseJeans, CoolShoes, barba cheia).
  Feminino continua sem roupa. Tudo trocável no criador.
- `ferramentas/etapa14_corpo.py`: mesma tabela. Saves antigos continuam válidos.

## Limites
- Cor do cabelo/roupas do John não copiada (segue a paleta do jogo). Olhos menores do John (eyeRoot) sem controle correspondente.
- Sem compilador aqui: o build do GitHub é a prova final. Força do masculino: `M_*` no topo de BodyMorph.kt.
