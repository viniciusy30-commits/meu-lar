# Etapa 97 — mãos e cabeça na corrida/pulo do corpo Sims 4 (aguardando teste)
- Mãos: o punho (fistHands) girava os dedos em torno de juntas medidas na mão do Sims 3 (FIST_J), ~4 cm fora no esqueleto do Sims 4, e rasgava os dedos ao correr/pular correndo. Agora o corpo Sims 4 usa FIST_J_TS4 (juntas de skel_s4.txt).
- Cabeça na corrida: no clipe 3 (correr) de clips_af5/clips_am5 a cabeça ficava ~15° (feminino) / ~11° (masculino) inclinada para trás, contra ~2° parada, enquanto o tronco inclina para a frente: olhava para cima e esticava o pescoço. Corrigido nos próprios clipes: pescoço (40%) e cabeça (60%) giram em X em torno das juntas até a cabeça ficar a ~3° (+18° feminino, +14° masculino). Verificado: sem folga nova entre tronco/pescoço/cabeça, escala intacta.
- Não mexe nos outros clipes (parado, andar, pulos, sentar).
- Se ainda olhar para cima/baixo demais: refazer com outro alvo (TARGET, em graus, hoje 3).
