# Etapa 101 — coxa atravessando a saia (Autumn Grace) de novo (aguardando teste)
- Causa: na etapa 98 o empurrão de cada vértice da saia passou a ter teto = folga que ele tinha na pose parada. Onde a saia já encostava na coxa parada (hem, fendas, quadril), a folga era menor que o raio da coxa e a colisão não empurrava nada: a perna atravessava de novo.
- Correção (CuteChar.legCollide): o vértice volta a ser empurrado até a superfície da coxa (raio medido no corpo + 0,9 cm de folga), sem o teto. Mantidos os ganhos de desempenho da etapa 98 (só vértices abaixo do quadril).
- Medido em simulação (Python, mesma matemática, corpo e clipes af5 reais, saia Autumn): pior atravessamento da saia dentro da perna, em cm — parado 5,7 -> 0,7; andar 5,9 -> 2,0; correr 6,0 -> 4,7 (antes da correção as 5 animações mais usadas ficavam em ~5,7 a 5,9).
- Só a saia Autumn Grace tem colisão (legCol). Sem compilador local: o build do GitHub é a prova final.
