"""Convierte capturas .raw de redux_shots.lua (f#####_WxH_BPP.raw) a PNG + hoja de contactos."""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def convert(p: Path) -> Path:
    w, h, bpp = map(int, re.search(r'_(\d+)x(\d+)_(\d+)\.raw$', p.name).groups())
    raw = p.read_bytes()
    if bpp == 16:
        px = np.frombuffer(raw, '<u2').reshape(h, w)
        rgb = (np.stack([px & 31, (px >> 5) & 31, (px >> 10) & 31], -1) << 3).astype(np.uint8)
    else:
        rgb = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
    out = p.with_suffix('.png')
    Image.fromarray(rgb).save(out)
    return out


def contact_sheet(pngs: list[Path], out: Path) -> None:
    ims = [Image.open(p).resize((320, 240)) for p in pngs]
    sheet = Image.new('RGB', (320 * len(ims), 240))
    for i, im in enumerate(ims):
        sheet.paste(im, (i * 320, 0))
    sheet.save(out)


if __name__ == '__main__':
    d = Path(sys.argv[1])
    pngs = [convert(p) for p in sorted(d.glob('*.raw'))]
    if pngs:
        contact_sheet(pngs, d / 'contact.png')
        print(*pngs, d / 'contact.png', sep='\n')
