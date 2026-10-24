"""G37 — rótulos de avisos del mapa en inglés: `SNMAP/KIEFETIM.BIN` entrada 3 (#271).

La hoja (TIM 4 bpp 256×256, VRAM (768,256), CLUT fila 4 = verde) guarda cada rótulo de 8 renglones como "sprite" que el
juego muestra con una animación: copias con renglones de más o de menos y/o corridas hacia abajo. Modelo verificado contra
el japonés (`selftest`): cada bloque = los primeros n renglones del rótulo completo, corrido `dy` renglones hacia abajo.

  grupos A/B/C (barreras, BARRIER HIT!!, SHIELD MISS!): 8 bandas por grupo, y = base + 7·k, n = k+1 (k = 0..7)
  D (斬り払い, 分身): 2 copias (dy 0 y 4) en las bandas (195,5) (202,6) (209,7) (216,8)
  E (クリティカル): 4 copias (dy 0,2,4,6) cada 48 px en las bandas (225,7) (232,8)

El inglés va en el estilo del propio juego (BARRIER HIT!!, SHIELD MISS!): mayúsculas de 5 renglones, contorno índice 1 en los
renglones 1 y 7, relleno 12/11/10/9/8 en los renglones 2–6. Fuente: 3×5 propia (M/W de 5, N de 4).

Uso:
  kief_labels.py selftest          regenera el japonés desde sí mismo y cuenta píxeles distintos (debe ser ~1)
  kief_labels.py render            escribe work/gfx/render/out/G37.png (+ G37_preview.png) desde work/gfx/render/G37.csv
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx_entrega as G  # noqa: E402
import tim  # noqa: E402

CSV = os.path.join(G.WORK, 'gfx', 'render', 'G37.csv')
OUT = os.path.join(G.WORK, 'gfx', 'render', 'out')
CLUT_ROW = 4
FILLS = [12, 11, 10, 9, 8]   # renglones 2..6
OUTLINE = 1

# Rótulos: caja x0, x1 (inclusive) del japonés en el renglón completo, y del renglón completo (8 renglones), ancho de celda
# (el rect del juego; el rótulo va centrado en él), copias [(x, dy)] y bandas [(y, n)].
BANDS8 = lambda base: [(base + 7 * k, k + 1) for k in range(8)]   # noqa: E731
LABELS = {
    'A1': dict(jp='イナーシャルキャンセラー', x0=0, x1=79, y=56, copies=[(0, 0)], bands=BANDS8(7)),
    'A2': dict(jp='ビームコート', x0=84, x1=123, y=56, copies=[(84, 0)], bands=BANDS8(7)),
    'A3': dict(jp='オーラバリア', x0=128, x1=174, y=56, copies=[(128, 0)], bands=BANDS8(7)),
    'A4': dict(jp='ピンポイントバリア', x0=180, x1=250, y=56, copies=[(180, 0)], bands=BANDS8(7)),
    'B1': dict(jp='Ｉ・フィールド', x0=3, x1=44, y=120, copies=[(3, 0)], bands=BANDS8(71)),
    'B2': dict(jp='ATフィールド', x0=48, x1=95, y=120, copies=[(48, 0)], bands=BANDS8(71)),
    'B3': dict(jp='念動フィールド', x0=103, x1=152, y=120, copies=[(103, 0)], bands=BANDS8(71)),
    'C1': dict(jp='グラビティ・テリトリー', x0=3, x1=76, y=184, copies=[(3, 0)], bands=BANDS8(135)),
    'C2': dict(jp='グラビティ・ウォール', x0=85, x1=154, y=184, copies=[(85, 0)], bands=BANDS8(135)),
    'D1': dict(jp='斬り払い', x0=54, x1=88, y=216, cell=48, copies=[(54, 0), (6, 4)],
               bands=[(195, 5), (202, 6), (209, 7), (216, 8)]),
    'D2': dict(jp='分身', x0=135, x1=152, y=216, cell=32, copies=[(135, 0), (103, 4)],
               bands=[(195, 5), (202, 6), (209, 7), (216, 8)]),
    'E1': dict(jp='クリティカル', x0=146, x1=189, y=232, cell=48, copies=[(146, 0), (98, 2), (50, 4), (2, 6)],
               bands=[(225, 7), (232, 8)]),
}
# Rótulos que ya están en inglés en el juego (no se tocan): BARRIER HIT!! (B4), SHIELD MISS! (C3)

# Fuente 3×5 (mayúsculas); M y W de 5, N de 4, I de 3, ! de 1
GLYPHS = {
    'A': '.#.|#.#|###|#.#|#.#', 'B': '##.|#.#|##.|#.#|##.', 'C': '.##|#..|#..|#..|.##', 'D': '##.|#.#|#.#|#.#|##.',
    'E': '###|#..|##.|#..|###', 'F': '###|#..|##.|#..|#..', 'G': '.##|#..|#.#|#.#|.##', 'H': '#.#|#.#|###|#.#|#.#',
    'I': '###|.#.|.#.|.#.|###', 'J': '..#|..#|..#|#.#|.#.', 'K': '#.#|#.#|##.|#.#|#.#', 'L': '#..|#..|#..|#..|###',
    'M': '#...#|##.##|#.#.#|#...#|#...#', 'N': '#..#|##.#|#.##|#..#|#..#', 'O': '.#.|#.#|#.#|#.#|.#.',
    'P': '##.|#.#|##.|#..|#..', 'Q': '.#.|#.#|#.#|##.|.##', 'R': '##.|#.#|##.|#.#|#.#', 'S': '.##|#..|.#.|..#|##.',
    'T': '###|.#.|.#.|.#.|.#.', 'U': '#.#|#.#|#.#|#.#|###', 'V': '#.#|#.#|#.#|#.#|.#.',
    'W': '#...#|#...#|#.#.#|##.##|#...#', 'X': '#.#|#.#|.#.|#.#|#.#', 'Y': '#.#|#.#|.#.|.#.|.#.',
    'Z': '###|..#|.#.|#..|###', '-': '...|...|###|...|...', '!': '#|#|#|.|#', ' ': '..|..|..|..|..',
}


def text_mask(text):
    """Máscara 5×w de `text` (mayúsculas), 1 px entre letras."""
    cols = []
    for ch in text.upper():
        rows = GLYPHS[ch].split('|')
        cols.append(np.array([[c == '#' for c in r] for r in rows], bool))
    w = sum(c.shape[1] for c in cols) + len(cols) - 1
    m = np.zeros((5, w), bool)
    x = 0
    for c in cols:
        m[:, x:x + c.shape[1]] = c
        x += c.shape[1] + 1
    return m


def label_image(text, width):
    """Rótulo completo 8×width (índices): outline renglones 1 y 7, relleno 12..8 en 2..6, centrado. None si no entra."""
    m = text_mask(text)
    if m.shape[1] > width:   # la tinta tiene que entrar; el contorno puede pasar 1 px por lado (hueco entre rótulos ≥ 4 px)
        return None
    img = np.zeros((8, width + 2), np.uint8)
    x = (width - m.shape[1]) // 2 + 1
    pad = np.pad(m, 1)
    dil = np.zeros_like(pad)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            dil |= np.roll(np.roll(pad, dy, 0), dx, 1)
    for (yy, xx), v in np.ndenumerate(dil):
        if v:
            img[2 + yy - 1, x + xx - 1] = OUTLINE   # contorno: renglones 1..7
    for (yy, xx), v in np.ndenumerate(m):
        if v:
            img[2 + yy, x + xx] = FILLS[yy]
    return img


def blocks(idx, key, F):
    """Escribe en idx todos los bloques del rótulo `key` a partir del rótulo completo F (8×w de la celda)."""
    L = LABELS[key]
    w = F.shape[1]
    off = cell_geometry(key)[1]
    for (x, dy) in L['copies']:
        x -= off + 1   # F lleva 1 px de margen a cada lado de la celda
        for (y, n) in L['bands']:
            canvas = np.zeros((n, w), np.uint8)
            for r in range(n):
                fr = r - dy
                if 0 <= fr < 8:
                    canvas[r] = F[fr]
            c0 = max(-x, 0)   # la primera columna de F cae fuera de la hoja si el rótulo empieza en x = 0
            cv = canvas[:, c0:]
            reg = idx[y:y + n, x + c0:x + c0 + cv.shape[1]]
            reg[cv != 0] = cv[cv != 0]


def clear(idx, key):
    L = LABELS[key]
    w = L['cell'] if 'cell' in L else L['x1'] - L['x0'] + 1
    off = (L['cell'] - (L['x1'] - L['x0'] + 1)) // 2 if 'cell' in L else 0
    ys = [y for y, n in L['bands']]
    y0, y1 = min(ys), max(y + n for y, n in L['bands'])
    for (x, dy) in L['copies']:
        idx[y0:y1, max(x - off - 1, 0):x - off + w + 1] = 0


def cell_geometry(key):
    """(ancho de celda, desfase del rótulo dentro de la celda) — el japonés está centrado en la celda."""
    L = LABELS[key]
    jw = L['x1'] - L['x0'] + 1
    return (L['cell'], (L['cell'] - jw) // 2) if 'cell' in L else (jw, 0)


def japanese_label(idx, key):
    L = LABELS[key]
    cw, off = cell_geometry(key)
    jw = L['x1'] - L['x0'] + 1
    F = np.zeros((8, cw + 2), np.uint8)
    F[:, 1 + off:1 + off + jw] = idx[L['y']:L['y'] + 8, L['x0']:L['x1'] + 1]
    return F


def load():
    data = open(os.path.join(tim.ISO, 'SNMAP', 'KIEFETIM.BIN'), 'rb').read()
    import lzpack
    raw = lzpack.read(data)[3]['raw']
    t = tim.scan(raw)[0]
    return raw, t, tim.indices(raw, t).copy()


def selftest():
    raw, t, idx = load()
    new = idx.copy()
    for key in LABELS:
        clear(new, key)
    for key in LABELS:
        blocks(new, key, japanese_label(idx, key))
    diff = int((new != idx).sum())
    ys, xs = np.where(new != idx)
    print(f'regenerado desde el japonés: {diff} píxeles distintos', list(zip(xs.tolist(), ys.tolist()))[:8])
    return diff


def rows():
    return list(csv.DictReader(open(CSV, encoding='utf-8')))


def render():
    raw, t, orig = load()
    idx = orig.copy()
    en = {r['caja']: r['en'] for r in rows()}
    jp_full = {key: japanese_label(orig, key) for key in LABELS}
    problems = []
    for key in LABELS:
        clear(idx, key)
    for key, L in LABELS.items():
        text = en.get(key, '')
        cw, off = cell_geometry(key)
        F = label_image(text, cw) if text else None
        if F is None:
            if text:
                problems.append(f'{key}: "{text}" no entra en {cw} px (mide {text_mask(text).shape[1] + 2})')
            F = jp_full[key]
        blocks(idx, key, F)
    os.makedirs(OUT, exist_ok=True)
    cl = tim.cluts(raw, t)
    tim.save_png(tim.indexed_png(idx, cl[0]), os.path.join(OUT, 'G37.png'))
    from PIL import Image
    pal = cl[CLUT_ROW]
    a = Image.fromarray(tim.bgr555(pal[orig]), 'RGBA')
    b = Image.fromarray(tim.bgr555(pal[idx]), 'RGBA')
    pv = Image.new('RGBA', (256 * 2 + 4, 256), (50, 50, 55, 255))
    pv.alpha_composite(a, (0, 0))
    pv.alpha_composite(b, (260, 0))
    pv.resize((pv.width * 3, pv.height * 3), Image.NEAREST).save(os.path.join(OUT, 'G37_preview.png'))
    for p in problems:
        print('AVISO', p)
    print('generado G37')
    return problems


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'selftest':
        sys.exit(0 if selftest() <= 4 else 1)
    elif cmd == 'render':
        render()
    else:
        print(__doc__)
