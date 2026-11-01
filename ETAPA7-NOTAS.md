# Etapa 7 — proporções do corpo e formato do rosto (aguardando teste no celular)

## O que entrou
- **Corpo > Proporções** (10 controles, -100..100, 0 = original): Altura, Peso, Ombros, Peito, Busto, Cintura, Quadril, Coxas, Braços, Cabeça.
- **Rosto > Formato** (13 controles): Masculinidade (rosto + pescoço), Cílios, Sobrancelha grossa, Ponte do nariz, Nariz largo, Nariz para baixo / para cima, Boca larga, Boca fina, Cantos dos olhos para baixo / para cima, Olhos quadrados, Orelha élfica.
- Botão "Zerar tudo" em cada lista; ímã no zero (-4..4 vira 0); salva ao soltar o controle.
- Save: `Avatar.encode` ganhou 23 números no fim (10 corpo + 13 rosto). Saves antigos continuam lendo (ficam em 0).

## Como funciona
- **Rosto**: `cute/morph.bin` (CMF1, 96 KB) tem os deslocamentos dos blendshapes do `BSMC_Head.fbx` já mapeados para os vértices do `base.bin` (as posições da cabeça do FBX batem exatamente com as do base). `CuteChar.refit` soma os deslocamentos nas posições de repouso do corpo-base. Gerado por `ferramentas/etapa7_morph_extrair.py` + `etapa7_morph_gerar.py`.
- **Corpo**: `BodyMorph.warp` é uma deformação suave aplicada às posições de REPOUSO de TODAS as malhas (corpo-base e peças) antes da pele, com a mesma função para todas — roupa, cabelo e sapatos acompanham. As matrizes de osso e os clips Idle/Walk/Jump NÃO foram tocados. Altura = escala final em torno dos pés (±6%).
- Só recalcula quando um controle muda (`shapeVer`), na thread GL, nas peças ativas.
- Se `morph.bin` faltar, o rosto fica sem controles (o resto funciona).

## Limites / decisões
- Os blendshapes de corpo do pack (BodyType, Chest, Weight) só existem nas CALÇAS no FBX (o corpo-base não os tem), então o corpo usa deformação por região, não blendshape. Faixas pequenas de propósito (até ~3 unidades de 162) para não atravessar roupa nem deformar a animação.
- Comprimento de pernas/braços não foi incluído: mexeria nas articulações e os pés afundariam/flutuariam em relação aos clips aprovados.
- Normais não são recalculadas (deslocamentos pequenos).
- Cabeças `Head_02` e `Head_SharpHead`: `Head_02` é a mesma forma da cabeça padrão com outra ordem de vértices; `SharpHead` difere menos de 1 unidade (~5 mm) e tem outra topologia. Não valem uma opção separada: o formato do rosto fica nos controles. Squareness, EarAngle e Weight de rosto do pack original não existem no `BSMC_Head.fbx` deste pack.
- Olhos: o pack só tem um modelo (`Eyes_BasicEyes`); a escolha continua sendo a cor (Rosto > Olhos).
- Roupas muito largas podem atravessar o corpo nos extremos (±100) de Peso/Coxas/Braços.
- Sem compilador aqui: o build do GitHub é a prova final. A matemática da deformação foi conferida com réplica em Python (`etapa7_warp_check.py`), sem NaN.

## O que testar
1. Corpo > Proporções: cada controle muda só a parte certa; roupa, cabelo e sapato acompanham sem atravessar.
2. Andar, pular e ficar parado continuam iguais (as animações não mudaram); sem pés flutuando com Altura em ±100.
3. Rosto > Formato: cada controle muda o rosto (close); Masculinidade também muda o pescoço.
4. Sair do criador, fechar e abrir o app: os valores continuam.
5. Saves antigos abrem com tudo em 0.
