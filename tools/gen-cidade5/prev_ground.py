from PIL import Image, ImageDraw
CO = {'asphalt': (74, 75, 80), 'curb': (230, 230, 225), 'sidewalk': (190, 150, 130), 'verge': (111, 168, 74), 'median': (96, 176, 70), 'island': (96, 176, 70), 'mark': (250, 250, 250), 'zebra': (255, 255, 255), 'tact': (214, 170, 70), 'prom': (226, 219, 201), 'prom2': (84, 84, 90), 'bike': (184, 69, 47), 'stairs': (255, 255, 255), 'pier': (139, 107, 71), 'wall': (120, 120, 126)}
ORDER = ['asphalt', 'verge', 'median', 'island', 'sidewalk', 'prom', 'prom2', 'bike', 'curb', 'wall', 'stairs', 'pier', 'mark', 'zebra', 'tact']
def crop(g, cx, cz, half, ppm, path, extra=None):
    S = int(2 * half * ppm); im = Image.new('RGB', (S, S), (106, 140, 90)); d = ImageDraw.Draw(im)
    def P(p): return ((p[0] - cx + half) * ppm, (p[1] - cz + half) * ppm)
    for lay in ORDER:
        for name, pts in g.layers:
            if name != lay: continue
            if all(abs(p[0] - cx) > half * 1.3 and abs(p[1] - cz) > half * 1.3 for p in pts): continue
            c = CO[lay]
            d.polygon([P(p) for p in pts], fill=c)
    im.save(path)
