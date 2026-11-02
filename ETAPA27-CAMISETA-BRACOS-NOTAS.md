# Etapa 27 — camiseta skatista refeita, cor da camisa e braços mais abertos (aguardando teste no celular)

Pedido: a camiseta ficou toda bugada; a parte de cima do braço (sovaco e bíceps) ficava muito colada no corpo, diferente do resto do braço; e não dava para mudar a cor da camisa.

## Camiseta (malha nova)
- Causa do "bugado": o tronco era alargado e o ombro "caído" empurrava a manga, o que formava bolas nos ombros e uma manga em trombeta. Agora o ombro quase não muda, a largura aumenta aos poucos até a barra, e a manga é um tubo solto em volta do braço (vai até perto do cotovelo).
- Manga inteira segue só o osso do braço (sem rasgar). Conferida em parado, andar e correr, por cima de jeans, bermuda e cargo.
- Barra desce ~22 cm (passa da cintura e cobre o quadril), corpo largo e reto.

## Cor da camisa
- Camiseta agora usa o sistema de cores normal: **Blusa** muda a cor da camisa e **Detalhe** a cor da estampa (sem escolher, a estampa acompanha a Blusa, um tom mais claro, como nas outras blusas). "Original" volta ao preto com estampa creme.
- Novos arquivos: `skatetee_recolor.png`, `skatetee_recolor_s.png`, `skatetee_recolor.txt`; `CuteColor.kt` ganhou a 4ª camada e `CuteChar.kt` sobe a textura recolorida.

## Braços do masculino
- No parado e no andar masculinos (clipes 4 e 5 do `base.bin`) a parte de cima do braço abre +7° e o antebraço volta 6°: o braço fica com a mesma inclinação do ombro à mão (~19-20°), sem encostar no sovaco; a mão fica a ~28 cm do centro (antes ~25), perto da coxa.
- Ajuste: `ferramentas/etapa27_postura_masculina.py` (variáveis ARM_ABD e FORE_BACK).

## Arquivos
`CuteColor.kt`, `CuteChar.kt`, `base.bin`, `p_top_skatetee.bin`, `skatetee.png`, `skatetee_recolor*.png/txt`, ferramentas `etapa27_camiseta_skate.py` e `etapa27_postura_masculina.py`.
Sem compilador/teste no aparelho aqui: o build é a prova final.

## Ajuste 28 (a partir do teste no celular)
- Mangas bem mais largas e compridas (camisa larga de verdade), com pequenas dobras.
- Folga calculada contra todas as calças/bermudas: o corpo da camisa é empurrado para fora do contorno delas (conferido em parado, andar e correr), então o short não atravessa mais.
- Tecido menos duro: dobras leves no corpo e barra ondulada.

## Ajuste 29
- Corpo da camisa refeito como um contorno liso (superelipse) que só alarga do peito para a barra, sem calombos nos quadris nem barriga.
- Folga contra calças/bermudas calculada por altura (e não por ângulo), então não aparecem mais bolhas.

## Ajuste 30
- Manga larga de ponta a ponta (sem formato de sino) e corpo solto no peito, sem ficar colado.

## Ajuste 31 (camiseta inchada)
- Causa do "inchado": o busto do corpo (feminino já nasce com busto) era aplicado também na camiseta larga e formava uma bola na frente. Agora a camiseta usa uma cúpula bem mais larga e suave (raio x1,8, altura x0,5, sem espalhar o tecido): cai reta, sem apertar o peito. Folga contra o corpo conferida (>=3 cm no busto padrão; encosta só no busto máximo).
- Mangas menos em balão: abertura mais contida (sk 1,7; sf 0,55), ainda larga e solta.
- Arquivos: `BodyMorph.kt` (parâmetro loose), `CuteChar.kt`, `p_top_skatetee.bin`, `ferramentas/etapa27_camiseta_skate.py`.

## Ajuste 32
- Pele do pescoço vazando em todas as roupas: a gola das blusas/vestidos seguia os ossos da coluna e o pescoço do corpo seguia os do pescoço/cabeça; ao mexer, a pele aparecia. Agora os pesos da gola (y > 139) são misturados com os do corpo (`ferramentas/etapa31_pescoco.py`, em todos os `p_top_*` e `p_overall_*`).
- Camiseta larga: ombro suavizado (sem as dobras na junção ombro/manga). Sovaco: a parte de baixo da manga agora segue mais o tronco (variável GUS no script), então o tecido não amassa nem abre embaixo do braço no parado/andar/correr (conferido com os clipes reais do base.bin). Triângulos do corpo escondidos: iguais aos originais.
