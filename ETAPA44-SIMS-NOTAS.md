# Etapa 44 — Corpos do Sims 3 (aguardando teste)

- O "Bozo" (base fofa) deixou de ser usado: todo personagem é um corpo do Sims 3 (malha, rosto, couro cabeludo e peles dos RARs do whiterider), ligado ao esqueleto do app (pesos copiados do base.bin por vizinho mais próximo, medidos na pose original do app; a malha final é posta com os braços para baixo).
- Criador (Base, Corpo e Rosto): Idade (Bebê, Criança, Jovem, Adulto, Idoso), Sexo, Corpo (Magro, Normal, Gordo) e Cabelo (Heartbeat ou careca; só jovem/adulto/idoso). Bebê e criança são unissex. A Julie (Personagens prontos) = mulher adulta normal.
- Tamanho: cada corpo é gravado na altura do adulto e o app o reduz pela idade (bebê 0,42, criança 0,68, masculino 0,986) via 5º campo do `pieces.txt`.
- "Normal" usa a malha `fit` do pack: a malha "normal" (`afbody`/`ambody`) vem sem pés e é quase igual. Peles ausentes no pack: teen masculino usa a pele do adulto; rosto teen usa o do adulto; bebê/criança usam suas peles.
- Roupa de baixo (top e short) pintada na pele, sem sobrepor roupa. Roupas e cabelos antigos (feitos para o Bozo) não aparecem nos corpos novos; as roupas novas virão do que o usuário mandar.
- Ajustes finos de corpo/rosto (sliders) não se aplicam aos corpos do Sims.
- Texturas de pele sobem sob demanda (`sk_*.png`), para não pesar na memória.
- Saves antigos: abrem como adulto normal (com cabelo), mantendo o sexo.
- Gerador: `python3 ferramentas/etapa44_sims.py <pasta com bodies/ faces/ skins/> app/src/main/assets/cute` (precisa de `etapa43_julie.py` ao lado, `base.bin`, `heartbeat.png`).
- Sem compilador local: o build do GitHub é a prova final.
