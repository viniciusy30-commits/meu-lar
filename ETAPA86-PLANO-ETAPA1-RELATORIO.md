# Plano Mestre v3 — ETAPA 1 (protótipo exigido pelo PDF): cadeira, mesa e armário com porta/gaveta

## Arquivos entregues
- GLB: app/src/main/assets/obj3d/int_cadeira_jantar.glb, int_mesa_jantar.glb, int_guarda_roupa.glb (texturas embutidas) + miniaturas em obj3d/thumb.
- Fonte/script: ferramentas/objetos3d/models_e1.py (+ glb_lib.py, geom.py, textures.py). Fichas técnicas: ferramentas/objetos3d/catalogo/{cozinha,quarto}/.
- Manifesto: ferramentas/objetos3d/catalogo/manifesto.json. Animação de interagir: ferramentas/etapa86_interagir.py -> assets/cute/clips_<g>.bin (9º clipe).

## O que cada ficha do PDF pede e como foi feito
- Cadeira de jantar: assento com espessura, encosto, pernas e travessas (sem pernas finas), altura de mesa e espaço para joelhos; estática no uso;
  ponto de sentar central voltado para a mesa; puxar a cadeira suave (desliza 0,55 s, sem salto) — antes de sentar e de volta depois.
- Mesa de jantar: tampo com espessura e bordas, pernas e reforços (cantoneiras), joelhos livres abaixo de 0,505 m, para 4 cadeiras (vagas nos metadados);
  estática; superfície para pratos/copos; pontos de sentar nas cadeiras; cadeira entra embaixo sem atravessar (colisão do tampo separada das pernas).
- Guarda-roupa: laterais, topo, base, fundo, portas com espessura, dobradiças, puxadores, prateleiras e cabideiro; interior modelado; ancorado;
  portas com dobradiça e limite (105°), gavetas com trilho (30 cm); ponto de interação frontal; parede/móvel testados antes de abrir;
  porta aberta bloqueia o personagem mas nunca o prende. Inventário de roupas (opcional no PDF): não feito.

## Testes feitos aqui
- Verificador GLB: 3/3 sem erros e sem avisos (estrutura, normais, faces, materiais, imagens, metadados, medidas).
- Glb.kt (código do jogo) compilado e executado na JVM: os 3 arquivos lidos; nós, pivôs, colisores, gatilho "puxar", pontos de sentar conferidos.
- Código novo compilado junto com o projeto: sem erros (só faltam as classes do SDK Android, que não existem aqui).
- Render: personagem real sentado na cadeira encaixada à mesa (joelhos sob o tampo, sem atravessar), guarda-roupa aberto/fechado.

## Testes obrigatórios do PDF que dependem do celular (pendentes)
Escala, posicionamento (colocar/girar/mover/encaixar a cadeira na mesa), colisão (andar em volta), partes móveis (abrir/fechar várias vezes),
interação (sentar/levantar em vários ângulos), interrupção (mexer o analógico no meio), persistência (salvar com portas/gavetas abertas e reabrir),
desempenho. A Etapa 2 só segue depois dessa validação.
