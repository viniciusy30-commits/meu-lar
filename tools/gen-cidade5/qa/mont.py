import sys
from PIL import Image
out = sys.argv[1]; fs = sys.argv[2:]; cols = 2
ims = [Image.open(f) for f in fs]; w, h = 800, 500
rows = (len(ims) + cols - 1) // cols
M = Image.new('RGB', (w * cols, h * rows), 'white')
for k, im in enumerate(ims): M.paste(im.resize((w, h)), ((k % cols) * w, (k // cols) * h))
M.save(out)
