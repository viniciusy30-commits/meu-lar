# Etapa 111 — camadas de roupa e regatas removidas

- Regatas baggy removidas do catálogo (ModStore.kt); as que estavam salvas como equipadas são tiradas. As miniaturas singlet_* em assets/cute/thumbs ficam sem uso (o fluxo de ZIP não apaga arquivos).
- Nova regra de camadas (mods/Layers.java + CuteChar.applyLayers): calça < camiseta < jaqueta. A peça de fora é empurrada para fora da de dentro (folga 1 cm, máximo 3 cm, espalhada em 3,5 cm), sempre a partir do repouso original (reversível ao trocar a combinação). Vale para jaqueta com capuz, calça cargo e peças Minimalist.
- Camiseta Minimalist some quando a jaqueta com capuz está vestida (a jaqueta já tem camisa branca por dentro; a barra da camiseta aparecia como faixa com dentes).
- A máscara de pele passa a considerar o empurrão (chave do cache inclui layerSig); regras de mãos e pés inalteradas.
- Aba branca da jaqueta mantida: ela cobre a pele da cintura (calça de cintura baixa).
- Ferramentas offline: ferramentas/mods_teste/LayerDump.java e MaskDump.java. Renderizações de prova em imagens-etapa111/.
- Limites conhecidos: jaqueta+cargo ainda tem um pequeno vão de pele na costura das costas e zíper um pouco bagunçado na frente. NÃO compilado no Kotlin nem testado no celular.
