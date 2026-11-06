# Etapa 103 — pele Llumisims Mercuria como pele padrão (aguardando teste)
- O .package da Mercuria traz camadas de detalhe cinza + alfa (não uma pele pronta). Formato de textura LRLE (V002) decodificado em `ferramentas/sims4/lrle.py` (blocos 4x4). Camada 11 = mulher adulta (rosto + corpo), 46 = homem adulto (as de bebê/criança/idoso/variações não foram usadas).
- `ferramentas/etapa103_mercuria.py` gera `sk_s4f.png` e `sk_s4m.png` (mesmo tamanho 1024x2048, mesmos UVs): detalhe da Mercuria multiplicado pelo tom da pele que o app já usava (sem estourar o vermelho).
- Padding preto das ilhas e sobras da Mercuria viram sangria da pele vizinha (sem fendas escuras no modelo); áreas sem dados (pés) ficam na cor lisa da canela.
- Preservado do atlas antigo: olho (canto esquerdo), boca/dentes, sobrancelhas e roupa de baixo (sutiã/calcinha, cueca) pintadas.
- Só 2 PNGs mudaram; código Kotlin e malhas intactos. Não testado no aparelho (não dá para renderizar o 3D aqui). Se algum ponto ficar estranho, mande print.
