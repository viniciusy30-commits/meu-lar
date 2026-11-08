# Etapa 126

- **Crash ao voltar ao jogo** (`glBufferData remaining() < size`): malhas só-GPU perdiam a cópia na memória e o contexto GL caía. `Part.upload()` agora devolve false nesse caso (a peça é pulada e a cidade é remontada) e `City.builtGen` usa a geração do GL do início da montagem.
- **Paredes/teto**: `setInside` só esconde paredes/teto na vista aérea (mode 1). Vista aérea na rua segue o jogador (`cityAer()`), com analógico (`GameView.aerialCityTouch`, `Overlay.drawJoy`) e toque para andar em linha reta. Câmera de 3ª pessoa fica dentro do prédio (limites do `City.Bld`).
- **Piscar (z-fighting)**: plano próximo maior fora de casa (0,3 m; 0,16 m dentro de loja; 0,35 m dirigindo); guia da calçada sem faces coincidentes; laje do topo das torres mais alta; reboco interno a 1,2 cm; moldura/vidro das janelas dos sobrados. O harness tem detector (`FIGHT=1 ./run.sh`).
- **Interiores**: `CityInt.kt` (hospital/PS/clínica, barbearia, salão, supermercado/mercadinho/conveniência, farmácia, banco/câmbio, academia, hotel, escola, polícia, bombeiros, portarias, shopping, restaurante) + pisos por tipo + texturas procedurais `Mt.GOODS` e `Mt.BOOKS`.
- **Direção**: física arcade com aderência lateral/derrapagem, freio de mão, marchas; pedais na tela (`gasIn/brakeIn/hbIn`), câmera de perseguição com FOV pela velocidade.
