from PIL import Image, ImageDraw
CO = {'asphalt': (74, 75, 80), 'curb': (230, 230, 225), 'sidewalk': (190, 150, 130), 'verge': (111, 168, 74), 'median': (111, 168, 74), 'mark': (250, 250, 250)}
ORDER = ['asphalt', 'verge', 'median', 'sidewalk', 'curb', 'mark']
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
