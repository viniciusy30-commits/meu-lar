# Etapa 40 - Tela de customizacao estilo The Sims 4 (CAS)

Aplicada sobre o main com Etapa 39 (inclui os "Personagens prontos").

- Sem o titulo "Meu personagem". Seta de voltar (canto superior esquerdo) fecha o criador e volta ao jogo
  (as escolhas ja sao salvas a cada toque).
- Categorias (Base, Corpo, Cabelo, Rosto, Roupa, Sapatos, Acessorios) em arco, bem espacadas, centralizadas
  na altura util da tela. Icone de cabelo novo (cabelo comprido com franja).
- Tudo centralizado no mesmo eixo: personagem, aneis, setas de girar e dado.
- Camera: 1 dedo = gira e inclina; 2 dedos = zoom (pinca) + mover a camera. Ao trocar de aba a camera volta ao enquadramento.
- Painel branco translucido, abas centralizadas, cartoes brancos, botao "Pronto" verde, dado que sorteia a aba atual.
- Fundo aqua e palco claro no 3D (Renderer3D.kt / Avatar.kt).
- Arquivos: Creator.kt, Ui.kt (icone BACK e HAIR), GameView.kt (toque), Renderer3D.kt (pitch/pan/fundo), Avatar.kt (palco).
- Sem compilador local: o build do GitHub e a prova final.
