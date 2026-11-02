# Etapa 37 — personagem pronto Zero YAM (aguardando teste no celular)

Pedido: colocar o personagem do arquivo `.sim` (Sims 3, "ZeroSliderBase YAM") na customização como personagem pronto, à parte, para escolher junto das bases masculina e feminina.

## O que o .sim tinha
- Pacote do Sims 3: só dados de aparência (homem adulto, sem cabelo, olhos vermelho-escuros, 8 roupas), sem malha 3D. A miniatura é só o logo "zero YAM". Por isso o app não carrega o arquivo: o visual foi convertido para peças que já existem.

## O que mudou
- `Avatar.kt`: `AvaPal.PRESET_N/PRESET_D` (lista de personagens prontos) e `Avatar.applyPreset(id)`. Zero YAM = `applyBase(true)` + sem cabelo, camiseta, calça social, descalço, sem barba, olhos cor 6. Mantém a pele. Formato do save não mudou.
- `Creator.kt`: na tela Base, seção "Personagens prontos" com um cartão por personagem (mesmo fluxo dos botões de base).
- `novidades.txt`: entrada nova.

## Limites
- Sem compilador aqui: o build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.
- As outras 7 roupas do .sim (smoking, jaqueta de motoqueiro, sunga etc.) não entraram; dá para virar mais personagens prontos.
