"""Atlas de texturas das placas (texto de verdade, fonte DejaVu Bold). O jogo usa este PNG como textura Mt.SIGN da Cidade 5."""
import math
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
AW, AH = 2048, 2048

def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except Exception: return ImageFont.load_default()

def center_text(d, box, text, fnt, fill, spacing=4):
    x0, y0, x1, y1 = box
    lines = text.split('\\n') if '\\n' in text else text.split('\n')
    tot = sum(d.textbbox((0, 0), l, font=fnt)[3] + spacing for l in lines) - spacing
    y = y0 + ((y1 - y0) - tot) / 2
    for l in lines:
        b = d.textbbox((0, 0), l, font=fnt); w = b[2] - b[0]
        d.text((x0 + ((x1 - x0) - w) / 2 - b[0], y - b[1]), l, font=fnt, fill=fill); y += (b[3] - b[1]) + spacing

class Atlas:
    def __init__(self):
        self.im = Image.new('RGBA', (AW, AH), (255, 255, 255, 255)); self.d = ImageDraw.Draw(self.im)
        self.uv = {}                  # chave -> (u0, v0, u1, v1) normalizado (v0 = topo)
        self.cx = 0; self.cy = 0; self.row_h = 0
        self.blade_y = 1024; self.blade_x = 0; self.blades = 0
        self.fixed()

    def place(self, key, w, h):
        if self.cx + w > AW: self.cx = 0; self.cy += self.row_h; self.row_h = 0
        x, y = self.cx, self.cy; self.cx += w; self.row_h = max(self.row_h, h)
        self.uv[key] = (x / AW, y / AH, (x + w) / AW, (y + h) / AH)
        return x, y

    def fixed(self):
        d = self.d
        # PARE (octogono)
        x, y = self.place('stop', 256, 256)
        pts = [(x + 128 + 124 * math.cos(math.radians(22.5 + 45 * i)), y + 128 + 124 * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
        d.polygon(pts, fill=(255, 255, 255)); pts2 = [(x + 128 + 112 * math.cos(math.radians(22.5 + 45 * i)), y + 128 + 112 * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
        d.polygon(pts2, fill=(204, 28, 28)); center_text(d, (x + 20, y + 80, x + 236, y + 176), 'PARE', font(70), (255, 255, 255))
        # DE A PREFERENCIA (triangulo para baixo): plano (0,-0.9)(1,0.75)(-1,0.75) -> tile
        x, y = self.place('yield', 256, 256)
        def T(px, py): return (x + (px * 0.5 + 0.5) * 256, y + (0.5 - py * 0.5) * 256)
        d.polygon([T(0, -0.9), T(1, 0.75), T(-1, 0.75)], fill=(204, 28, 28)); d.polygon([T(0, -0.55), T(0.62, 0.55), T(-0.62, 0.55)], fill=(255, 255, 255))
        center_text(d, (x + 70, y + 58, x + 186, y + 118), 'DÊ A\nPREFERÊNCIA', font(15), (204, 28, 28), 2)
        # velocidade
        for sp in (30, 40, 50, 60):
            x, y = self.place(f'speed{sp}', 256, 256)
            d.ellipse([x + 4, y + 4, x + 252, y + 252], fill=(204, 28, 28)); d.ellipse([x + 30, y + 30, x + 226, y + 226], fill=(255, 255, 255))
            center_text(d, (x + 30, y + 60, x + 226, y + 200), str(sp), font(104), (20, 20, 20))
        # losangos amarelos: extensao 1.1*size => mapeia [-1,1]
        def diamond(key, draw_icon):
            x, y = self.place(key, 256, 256)
            d.polygon([(x + 128, y + 2), (x + 254, y + 128), (x + 128, y + 254), (x + 2, y + 128)], fill=(20, 20, 20))
            d.polygon([(x + 128, y + 16), (x + 240, y + 128), (x + 128, y + 240), (x + 16, y + 128)], fill=(245, 197, 24))
            draw_icon(x, y)
        def ped(x, y):
            d.ellipse([x + 118, y + 62, x + 140, y + 84], fill=(20, 20, 20)); d.line([(x + 129, y + 86), (x + 129, y + 138)], fill=(20, 20, 20), width=9)
            d.line([(x + 129, y + 98), (x + 106, y + 122)], fill=(20, 20, 20), width=7); d.line([(x + 129, y + 98), (x + 152, y + 120)], fill=(20, 20, 20), width=7)
            d.line([(x + 129, y + 138), (x + 112, y + 176)], fill=(20, 20, 20), width=8); d.line([(x + 129, y + 138), (x + 148, y + 176)], fill=(20, 20, 20), width=8)
            for k in range(3): d.rectangle([x + 80, y + 186 + k * 9, x + 176, y + 190 + k * 9], fill=(20, 20, 20))
        diamond('pedestre', ped)
        def bump(x, y):
            d.pieslice([x + 78, y + 100, x + 178, y + 200], 180, 360, fill=(20, 20, 20)); d.rectangle([x + 70, y + 150, x + 186, y + 160], fill=(20, 20, 20))
            d.rectangle([x + 100, y + 70, x + 156, y + 98], fill=(20, 20, 20)); d.ellipse([x + 104, y + 92, x + 118, y + 106], fill=(20, 20, 20)); d.ellipse([x + 138, y + 92, x + 152, y + 106], fill=(20, 20, 20))
        diamond('lombada', bump)
        def rot(x, y):
            d.arc([x + 78, y + 78, x + 178, y + 178], 20, 340, fill=(20, 20, 20), width=11)
            for ang in (0, 120, 240):
                cx = x + 128 + 50 * math.cos(math.radians(ang)); cy = y + 128 + 50 * math.sin(math.radians(ang))
                d.polygon([(cx + 18 * math.cos(math.radians(ang + 90)), cy + 18 * math.sin(math.radians(ang + 90))), (cx - 18 * math.cos(math.radians(ang + 90)), cy - 18 * math.sin(math.radians(ang + 90))), (cx + 24 * math.cos(math.radians(ang)), cy + 24 * math.sin(math.radians(ang)))], fill=(20, 20, 20))
        diamond('rotatoria', rot)
        # FIM DA VIA (faixa larga)
        x, y = self.place('fim', 384, 128)
        st = Image.new('RGB', (384, 128), (255, 255, 255)); sd = ImageDraw.Draw(st)
        for k in range(-3, 14): sd.polygon([(k * 36, 0), (k * 36 + 18, 0), (k * 36 - 28, 127), (k * 36 - 46, 127)], fill=(204, 28, 28))
        sd.rectangle([28, 28, 355, 99], fill=(255, 255, 255)); self.im.paste(st, (x, y))
        center_text(d, (x + 28, y + 28, x + 355, y + 99), 'FIM DA VIA', font(46), (204, 28, 28))
        self.blade_y = self.cy + self.row_h + 8

    def blade(self, text):
        key = 'blade:' + text
        if key in self.uv: return key
        W, H = 256, 56
        if self.blade_x + W > AW: self.blade_x = 0; self.blade_y += H
        x, y = self.blade_x, self.blade_y; self.blade_x += W
        if y + H > AH: return 'blade:' + next(k for k in self.uv if k.startswith('blade:'))[6:]
        self.uv[key] = (x / AW, y / AH, (x + W) / AW, (y + H) / AH)
        d = self.d; d.rectangle([x, y, x + W - 1, y + H - 1], fill=(22, 105, 62)); d.rectangle([x + 3, y + 3, x + W - 4, y + H - 4], outline=(255, 255, 255), width=2)
        f = font(30)
        while d.textbbox((0, 0), text, font=f)[2] > W - 16 and f.size > 12: f = font(f.size - 2)
        center_text(d, (x, y, x + W, y + H), text, f, (255, 255, 255))
        self.blades += 1
        return key

    def save(self, path):
        self.im.convert('RGB').save(path)
