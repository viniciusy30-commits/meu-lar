# Etapa 100 — punho a partir do pulso (aguardando teste)
Causa: o clipe de correr (Sims 4) já tem os dedos numa pose relaxada gravada; o fistHands girava por cima dela e os dedos abriam em leque/tortos.
Correção (só CuteChar.kt, fistHands, só corpo Sims 4): a matriz de cada junta dos dedos é misturada com a do pulso (k) antes do giro do punho.
Não foi renderizado aqui (faltavam p_body_af5.bin e clips_af5.bin). Se ainda ficar torto, manda print.
