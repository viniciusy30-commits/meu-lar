# Etapa 95 — Blusa Bloom por cores + saia Autumn Grace (aguardando teste)
- Blusa renda Bloom: agora é um item único em Roupa > Blusas (corpo feminino do Sims 4), com 12 cores no seletor "Cor: Blusa Bloom". As malhas das 12 cores eram idênticas; só a textura troca.
- Saia Autumn Grace (GoldFish, pacote "Autumn Grace"): em Roupa > Calças, só no corpo feminino do Sims 4. Saia rodada de cintura alta com o cinto; o suéter do conjunto não foi incluído.
- 6 cores: xadrez mostarda, cinza, verde-oliva, ferrugem, azul petróleo e preta. As 5 pretas do pacote só mudavam a cor do detalhe do cinto, então ficou uma.
- Malha nativa (LOD0) na mesma escala da Bloom, afastada 0,5 cm da pele; modo da Bloom (sem esconder a pele, cortando por alfa). Pesos nativos do pacote, mas as coxas só com 55% do peso (o resto vai para a pelve) para a saia não esticar ao andar/correr.
- Seletor de cor generalizado (ModStore.VARS / setVariant): vale para Lotus, Bloom e Autumn. A cor escolhida fica salva em mods/variants.txt. Quem já tinha Lotus/Bloom colorido vestido é migrado para o item único com a mesma cor.
- Arquivos: ModStore.kt, Creator.kt, assets/cute/skate/autumn_af5.cup e autumn_<cor>.png, thumbs/autumn_mostarda_af5.png. Gerador: ferramentas/autumn/ (usa os módulos de ferramentas/bloomtop).
- Sobras sem uso (não apagadas): miniaturas bloom_<cor>_af5 exceto a branca.
- Não testado no aparelho; o build do GitHub é a prova final. A saia não tem simulação de tecido: coxas podem atravessar um pouco a barra em passadas largas.
