# Etapa 51 - Sem animacoes, corpo do Sims 3 como veio (aguardando teste)

Pedido: "retire todas as animacoes e eu quero o esqueleto e anatomia original do The Sims 3, do jeito que eles sao; remova qualquer coisa que nao seja do The Sims 3".

## O que mudou (so assets + ferramenta; Kotlin, shader e texturas NAO mudaram)
- `clips_{af,am,tf,tm,ef,em,cu,pu}.bin`: cada um agora tem 1 clipe de 1 quadro = pose original da malha do Sims 3 (so a escala cm->m), com a sola exatamente no chao.
  Sumiram: andar, correr, pulo, parado animado, balanco de bracos, dedos dobrados, correcao de cabeca/pescoco, bracos fechados (Etapas 47 a 49).
- `base.bin` e `f_1.bin` (restos do boneco antigo com animacoes do Mixamo): clipes trocados por 1 clipe parado. Arquivos menores (base 1,5 MB -> 0,5 MB).
- Malhas (`p_body_*.bin`), rostos, peles e sliders de corpo (Etapa 50) nao foram mexidos: ja eram a malha do Sims 3 so com escala uniforme.
- Ferramenta: `python3 ferramentas/etapa51_sem_animacao.py app/src/main/assets/cute`

## Limite importante
Os 3 RAR enviados (Bodies, Facesandscalps, Skins) tem so malhas OBJ e peles DDS: NAO trazem o esqueleto nem as animacoes do jogo.
As juntas continuam sendo as ajustadas na propria malha (Etapa 45), nos mesmos 55 ossos do app. Para o esqueleto REAL do Sims 3 (.skel / rig do Sims 3) e preciso enviar esse arquivo.

## Efeito no jogo
O personagem anda/corre/pula deslizando na pose original (bracos em A, como no Sims 3), sem mexer pernas ou bracos.
Piscar e expressoes do rosto continuam (sao do rosto, nao do corpo).
Cabelo Heartbeat, roupas e sapatos antigos nao foram removidos (nao fazem parte do esqueleto/anatomia); diga se quer tirar tambem.
