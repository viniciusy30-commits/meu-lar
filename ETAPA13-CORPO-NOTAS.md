# Etapa 13 — corpo masculino x feminino e busto maior (aguardando teste no celular)

Pedido: "tem que haver uma diferença entre corpo masculino e feminino" e "dê pra aumentar mais os peitos do corpo feminino, eles são muito pequenos".

## Situação antes
- O personagem tinha UM corpo só (a Mary, feminino). `Avatar.female` não era usado no personagem novo e o criador atual nem tinha botão de sexo.
- O controle Busto empurrava no máximo 2,6 cm, centrado em y=121, que fica abaixo do peito do modelo (o mamilo está em y≈127).
- O pack (Base Pack v2.1.5) só tem blendshapes de corpo nas calças (BodyType, Chest, Weight), não no corpo-base (ver `ETAPA7-NOTAS.md`). Não existe malha de corpo masculino separada, então a diferença vem de uma deformação própria, aplicada em todas as peças.

## O que mudou
- **Corpo > Proporções**: dois botões no topo, **Feminino / Masculino**. Salvo no `Avatar` (`masc`, último número do save; saves antigos abrem no feminino, igual a antes).
- **Masculino** = os mesmos controles somados a valores fixos: ombros +0,75, peito +0,6, cintura +0,55, quadril −0,6, braços +0,25, pescoço mais grosso, busto achatado (−1,5 cm), altura ×1,035 e Masculinidade do rosto +50%. Os sliders continuam funcionando por cima disso.
- **Feminino** = corpo original com busto-base +2,0 cm (já aparece mais que antes).
- **Busto**: duas cúpulas suaves empurradas para frente, centradas no peito de verdade (x=±9, y=127), mais largas em cima e mais cheias embaixo, com leve abertura para os lados e queda. O controle vai de −3 cm (−100%) a +8 cm (+100%) sobre o busto-base: em +100% o busto é bem grande.
- **Normais**: `BodyMorph.fixNormals` corrige o sombreado depois da deformação (soma à normal original a diferença entre normais suaves da malha deformada e da original; emendas de UV se cancelam). Sem isso o busto grande ficaria chapado. Vale também para o rosto (piscar/expressões) e para as roupas.
- Roupas, cabelo e sapatos usam a mesma função, então acompanham. Animações (Idle/Andar/Correr/Pulo) não mudaram.

## Conferência feita aqui
`ferramentas/etapa13_corpo.py` replica a fórmula em Python e renderiza o corpo de frente, ¾ e lado: feminino padrão, busto +50%, busto +100% e masculino padrão. Formas lisas, sem degraus, sem NaN. A versão Kotlin foi portada linha a linha das mesmas constantes.

## Limites / o que testar
1. Corpo > Proporções > Feminino/Masculino: o corpo muda na hora e o botão fica marcado; sair e abrir o app mantém.
2. Busto de −100 a +100 no feminino: forma arredondada, sem pontas; roupa acompanha (blusa, vestido, biquíni).
3. Masculino: peito reto, ombros largos; roupa e cabelo acompanham.
4. Cabelo comprido na frente do peito pode atravessar o busto grande (+60% ou mais). Se incomodar, a correção é empurrar o cabelo.
5. Sem compilador aqui: o build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.
