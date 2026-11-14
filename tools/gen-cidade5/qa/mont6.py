import sys, os, json
from PIL import Image, ImageDraw
d = sys.argv[1]; idx = json.load(open(os.path.join(d, 'index.json')))
w, h = 800, 509; per = 6
for m in range(0, len(idx), per):
    M = Image.new('RGB', (w * 2, h * 3), 'white'); D = ImageDraw.Draw(M)
    for q, it in enumerate(idx[m:m + per]):
        im = Image.open(os.path.join(d, f"t{it['k']:02d}.png")).resize((w, h)); M.paste(im, ((q % 2) * w, (q // 2) * h))
        D.rectangle(((q % 2) * w, (q // 2) * h, (q % 2) * w + 150, (q // 2) * h + 22), fill='black'); D.text(((q % 2) * w + 4, (q // 2) * h + 4), f"t{it['k']:02d} ({int(it['x'])},{int(it['z'])})", fill='white')
    M.save(os.path.join(d, f'm{m // per:02d}.png'))
