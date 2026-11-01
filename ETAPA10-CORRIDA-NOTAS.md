# Etapa 10 — animação de correr (aguardando teste no celular)

## Como funciona no jogo
- Analógico arrastado **quase até o limite** (≥ 88% do raio) = **correr** (velocidade fixa 2,6 m/s, casada com o clipe: sem pé deslizando). Arrasto leve = **andar** (como antes, velocidade proporcional ao arrasto).
- Histerese: começa a correr com ≥ 88% e só volta a andar abaixo de 70%, para não ficar alternando na borda.
- O botão do analógico fica **verde** enquanto corre.
- Troca andar ↔ correr suavizada (0,25 s) pelo mesmo sistema de blend dos outros clipes. Pulo continua igual (clipe Jump).

## O clipe (RUN = 4º clipe do `base.bin`, 0,62 s por ciclo, 49 quadros)
Gerado por cálculo de esqueleto (`ferramentas/etapa10_run.py` + `etapa10_skel.py`), validado contra o Walk do pack (a mesma matemática reproduz o Walk com erro < 0,5 mm):
- Pernas por cinemática inversa de 2 ossos: pé no chão se move para trás exatamente na velocidade do corpo (sem deslizar), fase de voo entre os passos, joelho alto na fase aérea, pouso com calcanhar/antepé e saída pela ponta do pé (dedos dobram, ficam no chão).
- Quadril sobe e desce (quique de ~6 cm), balança de lado e inclina (queda do quadril no lado que balança).
- Tronco inclinado para a frente (~9°), quadril e ombros girando em sentidos opostos, cabeça estabilizada olhando para a frente.
- Braços dobrados (~90°), balançando contra as pernas, cotovelos mais fechados quando o braço vai à frente; dedos relaxados como no Idle.
- Ciclo fecha sem salto (primeiro e último quadro idênticos). Roupas, cabelo, sapatos, proporções do corpo e expressões funcionam igual (usam os mesmos ossos).

## Arquivos
`base.bin` (+1 clipe), `CuteChar.kt` (constante RUN), `Renderer3D.kt` (decisão andar/correr, velocidade), `Ui.kt` (botão verde ao correr), ferramentas novas.

## Limites
- Sem compilador/aparelho aqui: só conferi o clipe numa renderização de silhuetas (lado e frente). O build do GitHub é a prova final.
- Cabelo longo e roupas largas não têm física própria: acompanham o corpo rígido.
- Se achar a corrida rápida/lenta ou o quique grande/pequeno, os números ficam no topo de `etapa10_run.py` (CYCLE, SPEED_M, H_AMP) e o limiar de corrida em `Renderer3D.kt` (0,88).
