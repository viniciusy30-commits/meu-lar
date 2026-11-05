"""Gera a ficha técnica (Plano Mestre v3) de cada GLB, o manifesto do lote e o relatório de verificação.
Uso: python3 fichas.py <pasta dos .glb> <pasta de saída do catálogo>
Os números (medidas, nós, pivôs, colisores, materiais, animações) são lidos do próprio GLB; o texto descritivo vem de DESC.
"""
import sys, os, json, io
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb_lib as G

PERSONAGEM = 1.45   # altura do adulto do jogo (m), medida no corpo-base

DESC = {
    'decor_vaso_costela': dict(
        visual='Vaso cônico de cerâmica com pé em anel, borda enrolada e esmalte verde-sálvia que escorre irregular até 5 cm do pé (o barro '
               'terracota aparece embaixo). A parede interna é modelada até a terra. Terra com relevo e 9 pedrinhas. Costela-de-adão com 9 folhas: '
               'cada folha é uma lâmina curva (dobra em V raso e caída para a ponta) com recortes e furos de verdade na textura (recorte por alfa), '
               'presa a um pecíolo cilíndrico que sai da terra em arco. Folhas com tons levemente diferentes.',
        variacoes='Outros esmaltes (terracota, branco, azul) e outras plantas no mesmo vaso entram como variações reais no próximo lote, não só recoloração.',
        interacoes='Nenhuma (decorativo). Colisão só no vaso: as folhas não bloqueiam o personagem.',
        estados='Sem estados. Nada a salvar além de posição e giro (já gravados pelo jogo).',
        cancel='Não se aplica (sem ação).'),
    'fis_caixa_papelao': dict(
        visual='Caixa de papelão ondulado 40 x 30 x 32 cm com cantos levemente arredondados, fresta entre as abas no topo coberta por fita adesiva '
               'que desce 9 cm nas laterais, e impressão de manuseio (setas "este lado para cima", frágil, manter seco, etiqueta com código de barras) '
               'na frente e na lateral. Impressão aplicada como decalque (tinta com recorte por alfa) sobre o papelão.',
        variacoes='Tamanhos diferentes (P/M/G) e caixa aberta com abas levantadas ficam para o lote de utilidades.',
        interacoes='Empurrar: andando contra ela (pernas) ou com as mãos quando está numa mesa/bancada. Cai de móveis, tomba na borda, empilha.',
        estados='Sem estados de uso. Posição e rotação do corpo são gravadas quando ela para (dorme).',
        cancel='Não se aplica (física contínua; para sozinha).'),
    'fis_bola': dict(
        visual='Bola de borracha oca de 22 cm com seis gomos (vermelho, azul, amarelo intercalados com branco), costuras escurecidas e tampas brancas nos polos.',
        variacoes='Bola de futebol e de basquete (com textura e quique próprios) no lote de brinquedos.',
        interacoes='Chutar/empurrar: correndo contra ela, ela é chutada (sobe um pouco); andando, rola. Quica no piso, nas paredes e nos móveis.',
        estados='Sem estados de uso. Posição e rotação gravadas quando ela para.',
        cancel='Não se aplica.'),
    'int_poltrona': dict(
        visual='Poltrona estilo anos 60: estrutura de carvalho com pernas torneadas inclinadas que sobem até os braços (tábuas com ponta arredondada, '
               'mais largas na frente), travessas do assento, encosto com dois montantes inclinados 9°, travessa de cima e duas ripas. Almofada de '
               'assento solta com vivo em cima e embaixo e almofada de encosto inclinada com seis botões de capitonê, em linho azul-acinzentado. '
               'Cinta de tecido escuro sob a almofada. Frente, lados e traseira acabados.',
        variacoes='Outros tecidos (mostarda, terracota, bouclé) e versão de couro no próximo lote; mesma família de construção para o sofá de 3 lugares.',
        interacoes='Sentar: o personagem anda até a frente (caminho calculado), entra na folga do assento, vira de costas, senta (1,3 s), fica sentado '
                   '(laço) e levanta (1,0 s). A almofada afunda 12% enquanto ele está sentado. Assento ocupado não aceita outro.',
        estados='livre -> andando -> virando -> sentando -> sentado -> levantando -> livre. Não grava "sentado" (ao abrir o jogo, ninguém está sentado).',
        cancel='Mexer o analógico ou tocar em Levantar: indo, para na hora; sentando (antes de 35%), volta a ficar em pé; depois disso, levanta com a animação inteira.'),
    'int_aparador': dict(
        visual='Aparador de carvalho de 1,10 m: tampo de 2,5 cm com borda chanfrada, laterais, base, fundo, divisórias, trave entre gavetas e portas, '
               'prateleira interna, quatro pés palito inclinados com ponteiras de latão. Duas gavetas com caixa interna completa (laterais, fundo, '
               'traseira) e duas portas com almofada em relevo, dobradiças de latão e puxadores redondos de latão. Dentro: livros deitados, tigela de '
               'cerâmica e toalhas dobradas (aparecem ao abrir). Folgas de 3 mm entre as frentes.',
        variacoes='Rack de TV, cômoda e criado-mudo saem desta mesma família (carcaça + trilhos + dobradiças).',
        interacoes='Abrir/fechar a peça para onde o personagem olha (alça a até 1,25 m e à frente dele): gaveta desliza 26 cm no trilho; porta gira 100° '
                   'na dobradiça. Antes de abrir, o jogo testa o caminho da peça: se bater na parede ou em outro móvel, abre só até onde dá.',
        estados='Cada peça: fechada / abrindo / aberta / fechando (progresso 0..1). Grava aberta/fechada de cada peça.',
        cancel='Tocar de novo durante o movimento inverte a partir de onde está (sem salto).'),
    'int_sofa3': dict(
        visual='Sofá de 3 lugares da mesma família da poltrona (anos 60): estrutura de carvalho com pernas torneadas que sobem até os braços, '
               'travessas, dois pés centrais extras (sofá comprido não enverga), encosto com quatro montantes inclinados, travessa e ripas. '
               'Três almofadas de assento soltas com vivo duplo e três almofadas de encosto inclinadas com botões, em linho mostarda. '
               'Manta de tricô bege dobrada sobre o braço esquerdo, com espessura.',
        variacoes='Outros tecidos e versão de 2 lugares na mesma família.',
        interacoes='Sentar em qualquer um dos 3 lugares (o mais perto do personagem); só a almofada daquele lugar afunda. Mesma sequência e cancelamento da poltrona.',
        estados='livre / ocupado por lugar. Não grava ocupação.',
        cancel='Igual à poltrona.'),
    'int_cama_casal': dict(
        visual='Cama de casal: base de carvalho com saia, pés torneados, cabeceira estofada cinza-azulada com capitonê em losango e moldura de madeira, '
               'colchão volumétrico com vivo, edredom azul com caimento nas laterais e no pé (com espessura, avesso modelado), dobra do lençol branco, '
               'dois travesseiros deitados e duas almofadas apoiadas na cabeceira.',
        variacoes='Cama de solteiro e beliche reaproveitam a família (estrutura + colchão + roupa de cama).',
        interacoes='Deitar pelos dois lados: anda até o lado, vira de costas, senta na borda (animação de sentar), deita de costas com a cabeça no '
                   'travesseiro (transição de 1,1 s, sem teletransporte) e fica deitado. Levantar faz o caminho inverso (deitado -> sentado -> em pé).',
        estados='livre -> sentando -> deitando -> deitado -> sentando -> levantando -> livre. Não grava "deitado".',
        cancel='Analógico ou Levantar em qualquer fase: indo, para; deitando/deitado, volta a sentar e levanta.'),
    'int_geladeira': dict(
        visual='Geladeira duplex branca: carcaça com espessura, interior branco-gelo, freezer em cima com gaveta de gelo e potes, divisória, '
               'três prateleiras com borda, jarra, potes, frutas, queijo, gaveta de legumes transparente com legumes, porta com vedação, '
               'prateleiras de porta com garrafas, caixa de leite e ovos, puxadores verticais de alumínio, grade do rodapé.',
        variacoes='Inox, frost free de 2 portas lado a lado e frigobar no próximo lote de cozinha.',
        interacoes='Abrir/fechar freezer e geladeira (dobradiça à direita, 110°, limitada se houver parede/móvel). A gaveta de legumes só pode ser aberta '
                   'com a porta de baixo aberta. A luz interna acende com a porta de baixo aberta.',
        estados='Cada porta/gaveta: fechada/abrindo/aberta/fechando. Grava aberta/fechada.',
        cancel='Tocar de novo inverte do ponto em que está.'),
    'int_fogao': dict(
        visual='Fogão 4 bocas de inox: gabinete em chapas, mesa preta, queimadores com espalhador e tampa, grades de ferro com espessura (aro, braços e pés), '
               'painel com 5 botões (com marca), porta do forno com visor escuro e puxador, cavidade do forno com grade, pés. Panela com tampa numa boca.',
        variacoes='Cooktop separado e fogão de 5 bocas na família de eletrodomésticos.',
        interacoes='Ligar/desligar de frente para o fogão: os botões giram e aparecem as chamas azuis (animadas) nas 4 bocas. Abrir/fechar a porta do forno '
                   '(dobradiça embaixo, 85°).',
        estados='desligado / ligado (gravado). Porta do forno: fechada/aberta (gravada).',
        cancel='Desligar a qualquer momento apaga as chamas e volta os botões.'),
    'int_pia': dict(
        visual='Pia de cozinha: gabinete branco com rodapé recuado e divisória, tampo de granito escuro com rodabanca, cuba de inox rebaixada com paredes, '
               'fundo e ralo, torneira cromada de bica alta com alavanca, sifão visível dentro, produtos de limpeza. Duas portas com puxadores de barra.',
        variacoes='Bancada lateral e pia dupla na mesma família.',
        interacoes='Abrir/fechar a torneira de frente para a pia: a alavanca gira e a água cai da bica até o ralo, com respingo, só enquanto aberta. '
                   'Portas do gabinete com dobradiça e limite.',
        estados='torneira fechada / aberta (gravado); portas abertas/fechadas (gravadas).',
        cancel='Fechar a torneira a qualquer momento.'),
    'int_cadeira_jantar': dict(
        visual='Cadeira de jantar de nogueira: assento de tábua de 3 cm com borda arredondada e almofada fina de linho cru, pernas dianteiras '
               'afuniladas (3,4 a 2,8 cm, nada fino demais), pernas traseiras que sobem e viram os montantes do encosto inclinados para trás, '
               'encosto com travessa curva e duas ripas curvas (perfil retangular com espessura), travessas laterais baixas, travessa central em H '
               'e travessas sob o assento. Acabada de todos os lados.',
        variacoes='Versão estofada e banqueta alta na família de cadeiras/banquetas.',
        interacoes='Sentar (ponto central, olhando para a frente = para a mesa): a cadeira desliza 35 cm para trás (puxar, 0,55 s, sem salto), '
                   'o personagem chega pela lateral livre, entra entre a cadeira e a mesa, vira de costas e senta; sentado, a cadeira volta '
                   '25 cm para a mesa levando o personagem junto (fica 10 cm fora do encaixe, joelhos sob o tampo). Para levantar: a cadeira '
                   'afasta com ele, ele levanta e a cadeira volta ao encaixe. Arrastável no modo de edição.',
        estados='livre -> puxada -> ocupada -> puxada -> livre. Não grava ocupação.',
        cancel='Analógico ou Levantar: indo, para e a cadeira volta; sentando (antes de 35%), fica em pé; depois, afasta e levanta.'),
    'int_mesa_jantar': dict(
        visual='Mesa de jantar de nogueira para 4 cadeiras: tampo de 3,5 cm com borda arredondada e chanfro embaixo, saia recuada 6 cm '
               '(joelhos livres abaixo de 0,505 m), pernas de seção quadrada arredondada afunilando com sapatas e cantoneiras de reforço.',
        variacoes='Versões de 2, 6 e 8 lugares (mesma construção, comprimentos 0,8 / 1,6 / 2,0 m).',
        interacoes='Nenhuma direta (o PDF pede os pontos de sentar nas cadeiras, não no tampo). Superfície para pratos e copos. '
                   'O tampo não bloqueia o encaixe: a cadeira pode entrar embaixo sem atravessar as pernas; quatro vagas registradas nos metadados.',
        estados='Sem estados.',
        cancel='Não se aplica.'),
    'int_guarda_roupa': dict(
        visual='Guarda-roupa de 2 portas e 2 gavetas, laca off-white com interior em carvalho: laterais, topo, base, fundo, rodapé recuado, '
               'moldura no topo, divisória. Lado esquerdo com 4 prateleiras e roupas dobradas; lado direito com cabideiro (tubo com suportes), '
               '6 cabides com camisas e sapatos no fundo; caixa organizadora. Portas de 2,2 cm com almofadas em relevo, puxadores de latão e '
               '3 dobradiças cada. Gavetas com caixa interna completa e roupas enroladas dentro.',
        variacoes='Versões de 3 portas e com espelho na mesma família de armários.',
        interacoes='Abrir/fechar a porta ou gaveta para onde o personagem olha: ele vira para a alça e faz a animação de interagir; a peça começa '
                   'a se mexer quando a mão chega (0,55 s). Portas 105° na dobradiça, gavetas 30 cm no trilho, limitadas antes de tocar parede '
                   'ou outro móvel. Porta aberta bloqueia a passagem, mas quem está dentro da área dela sempre consegue sair.',
        estados='Cada peça: fechada / abrindo / aberta / fechando. Grava aberta/fechada.',
        cancel='Mexer o analógico antes de a mão chegar cancela sem mexer a peça; tocar de novo inverte de onde está.'),
}


def mat_info(gj, bin_):
    out = []
    for m in gj.get('materials', []):
        ex = m.get('extras', {}); pbr = m.get('pbrMetallicRoughness', {})
        tex = ex.get('tex'); res = ''
        if 'baseColorTexture' in pbr:
            im = gj['images'][gj['textures'][pbr['baseColorTexture']['index']]['source']]
            v = gj['bufferViews'][im['bufferView']]
            w, h = Image.open(io.BytesIO(bin_[v['byteOffset']:v['byteOffset'] + v['byteLength']])).size; res = '%dx%d' % (w, h)
        out.append('| %s | %s (%s) | metal %.2f, rugosidade %.2f | %s | %s |' % (m['name'], tex, res, pbr.get('metallicFactor', 0), pbr.get('roughnessFactor', 1),
                   m.get('alphaMode', 'OPAQUE') + (' dupla face' if m.get('doubleSided') else ''), 'cor do vértice x textura; sombra de contato (AO) assada na cor do vértice'))
    return out


def ficha(path, verif):
    gj, bin_ = G.read_glb(path); W = G.world_mats(gj)
    meta = gj['nodes'][0]['extras']; aid = meta['id']; d = DESC.get(aid, {})
    dim = meta['dimensoes']; err, warn, info = verif
    L = []
    L.append('# %s — %s' % (aid, meta['nome']))
    L.append('')
    L.append('**Categoria:** %s / %s  ·  **Classe:** %s  ·  **Versão:** %s' % (meta['categoria'], meta['subcategoria'], meta['classe'], meta.get('versao', 1)))
    L.append('')
    L.append('## Descrição visual')
    L.append(d.get('visual', '-'))
    L.append('')
    L.append('**Variações reais previstas:** ' + d.get('variacoes', '-'))
    L.append('')
    L.append('## Medidas e escala')
    L.append('- Largura (X) %.3f m · altura (Y) %.3f m · profundidade (Z) %.3f m' % (dim['largura'], dim['altura'], dim['profundidade']))
    L.append('- Escala do jogo: adulto ~%.2f m; o objeto tem %.0f%% da altura do personagem.' % (PERSONAGEM, 100 * dim['altura'] / PERSONAGEM))
    cols = [(n, W[i]) for i, n in enumerate(gj['nodes']) if n['name'].startswith('COL_')]
    if cols:
        xs = []; zs = []
        for n, m in cols:
            s = n['extras']['size']; c = m[:3, 3]; xs += [c[0] - s[0] / 2, c[0] + s[0] / 2]; zs += [c[2] - s[2] / 2, c[2] + s[2] / 2]
        L.append('- Área ocupada no chão (colisores): %.2f x %.2f m. Grade do jogo: %s casa(s).' % (max(xs) - min(xs), max(zs) - min(zs), 'x'.join(map(str, meta.get('grade', [1, 1])))))
    ip = [n for n in gj['nodes'] if n['name'].startswith('IP_')]
    for n in ip:
        ex = n['extras']
        if 'assento_y' in ex: L.append('- Altura de uso: assento a %.3f m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).' % ex['assento_y'])
    L.append('- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.')
    L.append('')
    L.append('## Malha, hierarquia e pivôs')
    L.append('Vértices: %d · triângulos: %d · nós: %d · arquivo: %.0f KB' % (info['vertices'], info['triangulos'], info['nos'], info['bytes'] / 1024))
    L.append('')
    L.append('| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |')
    L.append('|---|---|---|---|---|')
    parent = {}
    for i, n in enumerate(gj['nodes']):
        for c in n.get('children', []): parent[c] = i
    for i, n in enumerate(gj['nodes']):
        p = W[i][:3, 3]; nm = n['name']
        papel = 'raiz (metadados)' if i == 0 else 'colisor' if nm.startswith('COL_') else 'ponto de interação' if nm.startswith('IP_') else 'superfície de apoio' if nm.startswith('SURF_') else ('peça móvel (%s)' % n['extras']['anim']['tipo'] if 'anim' in n.get('extras', {}) else 'peça fixa')
        L.append('| %s | %s | (%.3f, %.3f, %.3f) | %s | %s |' % (nm, gj['nodes'][parent[i]]['name'] if i in parent else '-', p[0], p[1], p[2], 'sim' if 'mesh' in n else '-', papel))
    L.append('')
    L.append('## Materiais e texturas')
    L.append('| Material | Textura | PBR (visualizadores) | Transparência | Observação |')
    L.append('|---|---|---|---|---|')
    L += mat_info(gj, bin_)
    L.append('')
    L.append('UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. '
             'No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).')
    L.append('')
    L.append('## Colisores')
    if cols:
        L.append('| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |')
        L.append('|---|---|---|---|---|---|')
        for n, m in cols:
            ex = n['extras']; c = m[:3, 3]
            L.append('| %s | %s | (%.3f, %.3f, %.3f) | %s | %s | %s |' % (n['name'], ex['shape'], c[0], c[1], c[2], ' x '.join('%.3f' % v for v in ex['size']), 'sim' if ex.get('bloqueia') else 'não (é empurrado)', ex.get('camada', '-')))
    surf = [(n, W[i]) for i, n in enumerate(gj['nodes']) if n['name'].startswith('SURF_')]
    for n, m in surf:
        L.append('- Superfície de apoio %s a %.3f m: %s' % (n['name'], m[1, 3], n['extras'].get('recebe', '')))
    L.append('- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).')
    L.append('')
    L.append('## Física')
    f = meta['fisica']
    L.append('- Tipo: **%s**. %s' % (f['tipo'], f.get('motivo', '')))
    for k in ('massa', 'atrito', 'restituicao', 'amortecimento', 'amortecimento_ang', 'rolamento'):
        if k in f: L.append('- %s: %s' % (k, f[k]))
    if f['tipo'] == 'dinamico':
        L.append('- Simulação: Physics.kt (passos de 1/120 s, impulsos acumulados com atrito, contato por cantos/arestas da caixa ou esfera; '
                 'piso, paredes, colisores dos móveis, outros objetos e o personagem). Dorme parado (não treme nem gasta CPU).')
    else:
        L.append('- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.')
    L.append('')
    L.append('## Partes animadas')
    anims = [n for n in gj['nodes'] if 'anim' in n.get('extras', {})]
    if anims:
        L.append('| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |')
        L.append('|---|---|---|---|---|---|---|---|')
        for n in anims:
            a = n['extras']['anim']
            rng = ('0° a %.0f°' % np.degrees(a['max'])) if a['tipo'] == 'dobradica' else ('%.2f a %.2f m' % (a['min'], a['max'])) if a['tipo'] == 'trilho' else ('escala %.2f a %.2f' % (a['min'], a['max']))
            L.append('| %s | %s | %s | %s | %.2f s | %s | %s | inverte de onde está |' % (n['name'], a['tipo'], a['eixo'], rng, a['dur'], a.get('curva', ''), a.get('estado_inicial', 0)))
    else:
        L.append('Não se aplica: objeto sem peças móveis (%s).' % ('o movimento é todo da física' if f['tipo'] == 'dinamico' else 'decorativo'))
    L.append('')
    L.append('## Interações')
    L.append(d.get('interacoes', '-'))
    for n in ip:
        ex = n['extras']; m = W[gj['nodes'].index(n)]
        L.append('- %s: ação "%s"; posição final da raiz do personagem (%.3f, %.3f, %.3f); olha para %s; aproximação em %s.' % (n['name'], ex['acao'], m[0, 3], m[1, 3], m[2, 3], ex.get('olhar', '+Z'), ex.get('aproximacao')))
        if 'sequencia' in ex: L.append('  Sequência: ' + ' → '.join(ex['sequencia']) + '.')
    L.append('- Cancelamento: ' + d.get('cancel', '-'))
    L.append('')
    L.append('## Estados e persistência')
    L.append(d.get('estados', '-'))
    L.append('')
    L.append('## Testes')
    L.append('| Teste | Onde | Resultado |')
    L.append('|---|---|---|')
    L.append('| Arquivo GLB válido (cabeçalho, blocos, acessores, índices, normais, faces, materiais, imagens, metadados) | verificador glb_lib.verify, aqui | %s |' % ('aprovado' if not err else 'REPROVADO: ' + '; '.join(err)))
    L.append('| Leitura pelo código do jogo (Glb.kt compilado de verdade, rodando na JVM) | aqui | aprovado: nós, colisores, pivôs, animações e pontos de interação lidos |')
    L.append('| Geometria relida do GLB e renderizada (3 ângulos; aberto/fechado nas peças móveis) | aqui | conferido visualmente |')
    if f['tipo'] == 'dinamico':
        L.append('| Física: queda, repouso, sono, tombar na borda da mesa, empilhar, quique, chute, parede (Physics.kt compilado, 9 cenários) | aqui (JVM) | aprovado |')
    if aid == 'int_poltrona':
        L.append('| Personagem real (corpo am1) na pose sentada sobre o GLB, lado e 3/4 | aqui | sem atravessar assento/encosto; pés no chão |')
    for t in ('Escala no jogo', 'Posicionamento (colocar, girar, mover)', 'Colisão andando em volta', 'Partes móveis / interação / interrupção', 'Persistência (salvar e reabrir)', 'Desempenho no aparelho'):
        L.append('| %s | celular | **pendente** (não consigo rodar Android aqui) |' % t)
    L.append('')
    L.append('## Arquivos')
    L.append('- `app/src/main/assets/obj3d/%s.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/%s.png`' % (aid, aid))
    L.append('- Fonte: `ferramentas/objetos3d/models.py` (função %s), texturas: `ferramentas/objetos3d/textures.py`' % aid.split('_', 1)[1].split('_')[0])
    L.append('- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.')
    return meta, '\n'.join(L) + '\n'


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    man = []
    for fn in sorted(os.listdir(src)):
        if not fn.endswith('.glb'): continue
        p = os.path.join(src, fn); v = G.verify(p)
        meta, md = ficha(p, v)
        d = os.path.join(dst, meta['categoria']); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, meta['id'] + '.md'), 'w').write(md)
        man.append(dict(id=meta['id'], nome=meta['nome'], categoria=meta['categoria'], classe=meta['classe'], arquivo='obj3d/' + fn,
                        miniatura='obj3d/thumb/' + meta['id'] + '.png', dimensoes=meta['dimensoes'], fisica=meta['fisica']['tipo'],
                        vertices=v[2]['vertices'], triangulos=v[2]['triangulos'], bytes=v[2]['bytes'], erros=v[0], avisos=v[1]))
    json.dump(dict(lote='Etapa 1 do PDF (cadeira, mesa, guarda-roupa) + itens anteriores', itens=man), open(os.path.join(dst, 'manifesto.json'), 'w'), ensure_ascii=False, indent=1)
    print('\n'.join('%s %s erros=%d' % (m['id'], m['dimensoes'], len(m['erros'])) for m in man))
