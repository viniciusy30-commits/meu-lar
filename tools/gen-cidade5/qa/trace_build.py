import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geo as G, assemble, math
from assemble import City, elen
geo = G.Geo(); c = City(geo)
def rep(tag):
    L = sum(elen(e['p']) for e in c.edges); bm = sum(elen(e['p']) for e in c.edges if e.get('name') == 'Av. Beira-Mar'); lg = sum(elen(e['p']) for e in c.edges if 'Lagoa' in e.get('name','')); og = sum(elen(e['p']) for e in c.edges if 'Orla' in e.get('name',''))
    print(f'{tag:22s} arestas {len(c.edges):4d}  km {L/1000:6.1f}  beira-mar {bm:6.0f}  lagoa {lg:5.0f}  orla {og:6.0f}')
rep('inicio')
steps = 'add_beach_avenue lagoon_ring river_bridges connect_components red_bridges fix_dead_ends connect_components dedupe contract_short fix_acute fix_dead_ends contract_short merge_degree2 clean_polylines simplify_polylines fillet_polylines fix_close_parallel fix_dead_ends connect_components contract_short fix_acute fix_dead_ends connect_components merge_degree2 clean_polylines simplify_polylines fillet_polylines make_rounds flags repair_overlaps fix_acute resolve_bulbs merge_degree2 clean_polylines relax_tight_curves drop_tight_edges make_rounds flags'.split()
for s in steps:
    getattr(c, s)(); rep(s)
