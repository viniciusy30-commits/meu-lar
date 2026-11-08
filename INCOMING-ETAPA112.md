# Pacote de correção — Etapa 112 (Dunk High)

Este ZIP deve ser enviado diretamente à pasta `_incoming/` do repositório.

- Não precisa extrair manualmente.
- O workflow `Unpack and commit` extrai os caminhos do ZIP na raiz do projeto e cria o commit.
- Depois da extração, o workflow Android deve iniciar o build do APK.

O pacote inclui o tênis VHSync Dunk High no catálogo masculino de Sapatos, as 38 texturas, a miniatura e o conversor atualizado. A correção remove a deformação preta na ponta/sola: sapatos não passam mais pelo `pushOut` de tecido, e o CUP1 oculta os 570 triângulos do pé-base enquanto o tênis está vestido. A miniatura 3D também respeita essa máscara.

O package original StandStillInCAS é preservado. Ele contém tuning ASM XML do CAS do The Sims 4, não uma malha ou animação que o Meu Lar consiga executar.

Consulte `ETAPA112-DUNK-HIGH-STANDSTILL-NOTAS.md` para os detalhes técnicos, renders e limites do teste.
