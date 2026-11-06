# Etapa 107 — jaqueta com capuz e calça cargo: bugs visuais corrigidos + versão masculina (aguardando teste)
- Bug (manchas escuras/brancas): a malha tinha duas cascas coladas, a de dentro com normais virados para o corpo. Corrigido invertendo essas normais (hood_af5.cup e hcargo_af5.cup; posições/UVs/pesos intactos). Na camisa branca da barra da jaqueta, 1.246 triângulos duplicados de dentro foram apagados.
- Homem: novas peças hood_am5.cup e hcargo_am5.cup (corpo masculino do Sims 4), geradas por ferramentas/etapa107_jaqueta_calca_homem.py; mesmas 6 cores. ModStore.kt ganhou os itens hood_am5 / hcargo_am5 (grupo "am").
- Miniaturas masculinas são cópia das femininas (mesma peça).
- Não testado no aparelho; o build do GitHub é a prova final.
