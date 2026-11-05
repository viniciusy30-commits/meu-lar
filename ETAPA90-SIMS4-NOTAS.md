# Etapa 90 — Sims 4 (teste)
- Corpos am5/af5 convertidos dos OBJ enviados (ferramentas/etapa90_sims4.py), escalados para o esqueleto Sims 3 e pesos transferidos de am1/af1.
- Cabeça usa o atlas do Sims 4; olhos gerados (esferas). Corpo: o OBJ veio com o canal de UV errado, então a pele do corpo foi assada a partir da pele Sims 3.
- Sem cabelo/cílios ainda. Não testado no aparelho.

## 90b — textura certa do corpo
- O OBJ do corpo trazia só o UV1. O UV0 (atlas do TS4) foi tirado das roupas de baixo padrão do pacote "Softe" (akalukery): mesmo corpo da EA, então a posição igual dá o UV0 exato; o homem usa o corpo da mulher para tronco/braços.
- Ferramentas: ferramentas/sims4/dbpf.py (lê .package do TS4), geom.py (lê GEOM), uvfix.py.
- Pés: o pacote não tem pés (vêm dos sapatos) -> cor lisa de pele.
- A pele Mercuria (.package) não foi usada: o atlas enviado já tem a pele.

## 90c — acabamento (pescoço, nuca, ombros, pés)
- Pescoço/nuca: o corpo é cortado exatamente na volta de vértices onde a cabeça detalhada encaixa (antes sobravam triângulos sobrepostos: anel escuro e fresta na nuca). Pesos suavizados só na cabeça/pescoço.
- Ombros: atlas sem a linha escura das bordas das ilhas; triângulos entre duas ilhas recebem cor lisa (sem faixa esticada). Normais soldadas nas costuras.
- Pés: ganham o tamanho/posição do pé do Sims 3 (não atravessam mais os sapatos), cor lisa com degradê no tornozelo.
