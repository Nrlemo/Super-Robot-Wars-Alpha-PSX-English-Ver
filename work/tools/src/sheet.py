"""Hoja de contactos en grilla de las capturas f*.png de una carpeta: sheet.py <dir> [salida.png] [columnas]"""
import glob, os, sys
from PIL import Image, ImageDraw

d = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(d, 'sheet.png')
cols, w, h = int(sys.argv[3]) if len(sys.argv) > 3 else 6, 320, 240
fs = sorted(glob.glob(os.path.join(d, 'f*.png')))
S = Image.new('RGB', (cols * w, ((len(fs) + cols - 1) // cols) * h))
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB').resize((w, h))
    ImageDraw.Draw(im).text((3, 3), os.path.basename(f)[:6], fill=(255, 255, 0))
    S.paste(im, ((i % cols) * w, (i // cols) * h))
S.save(out)
print(out, len(fs))
