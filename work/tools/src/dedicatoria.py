"""Pantalla de dedicatoria después del copyright (#279): dedicatoria (castellano) + 2 QR con rótulo (inglés).

No hay textura nueva: la pantalla usa la misma hoja G20 (`TITLE/TITLEDAT.BIN` #2) y la misma tabla de sprites del
copyright (12 sprites, 3 secuencias en TITL: entrada, quieto, salida). La hoja se **reempaqueta**: los 12 recortes del
copyright (ya en inglés, de la etapa "graphics") y los 12 de la pantalla nueva conviven en 256×240. Los registros del
copyright en TITL apuntan a su nueva posición (u, v), y la pantalla nueva reescribe en tiempo de ejecución los campos de
los 36 registros (tamaño, dx, dy, uv, medio ancho y medio alto) y los restaura antes del video.

Código (armips, `patches/dedicatoria.asm`) en la cola libre del último sector de `OVL/MOVE_GRP.BIN` (1.480 B, cargada
en 0x80114AC4; ver notes/graficos.md § "Pantalla propia después del copyright"): el archivo crece dentro de su sector y
no se corre ningún LBA. Dos enganches en TITL:
  0x80104700  jal 0x80106328 → jal ded_hold     (estado 2: con la dedicatoria, el contador avanza a medio paso)
  0x801047E4  jal 0x80104888 → jal ded_next     (estado 4: 1.ª vez → pantalla nueva; 2.ª → video, como el original)

Paleta (CLUT de G20, 16 colores; el copyright usa 0, 1 y 15): se agregan los colores de COLORS.

Uso:
  dedicatoria.py build <TITLEDAT_in> <TITL_in> <dir_salida>   → TITLE/TITLEDAT.BIN, OVL/TITL_GRP.BIN, OVL/MOVE_GRP.BIN
  dedicatoria.py preview <TITLEDAT_in> <TITL_in> <png>          hoja + simulación de las dos pantallas
"""
import glob
import os
import struct
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import tim  # noqa: E402
import copyright_patch  # noqa: E402

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLS = os.path.join(WORK, 'tools')
# carpetas donde se buscan las TTF (las mismas que gfx_render.py; en Debian/Ubuntu vienen en fonts-dejavu-extra)
FONT_DIRS = [os.path.join(WORK, 'gfx', 'fonts'), '/usr/share/fonts', '/usr/local/share/fonts',
             os.path.expanduser('~/.local/share/fonts')]
G20 = 2                                   # TIM #2 de TITLEDAT.BIN
TITL_BASE = 0x800FF190
MOVE_BASE = 0x8011308C
MOVE_SECTORS = 4

DEDICATORIA = ('Dedicado a mi Familia (E y O), a mi amigo Pablo M. (Fan de SRW) y a todos los que durante tantos '
               'años hicieron posible jugar los mejores juegos.')
# cortes a mano (renglones parejos y sin partir los paréntesis); cada uno ≤ 254 px con la sombra
DED_LINES = ['Dedicado a mi Familia (E y O),', 'a mi amigo Pablo M. (Fan de SRW)',
             'y a todos los que durante tantos años', 'hicieron posible jugar los mejores juegos.']
assert ' '.join(DED_LINES) == DEDICATORIA
DED_FONT = ('DejaVuSansCondensed-Bold', 12)
HEADING = 'Contribute to this project:'
HEAD_FONT = ('DejaVuSansCondensed-Bold', 12)
LABEL_FONTS = (('DejaVuSansCondensed-Bold', 11), ('DejaVuSansCondensed-Bold', 10))
QRS = [  # (texto del QR, error, rótulo 1, rótulo 2)
    ('HTTPS://GITHUB.COM/NRLEMO/SUPER-ROBOT-WARS-ALPHA-PSX-ENGLISH-VER', 'L', 'GitHub', 'Updates & bug reports'),
    ('https://buymeacoffee.com/srwa_en', 'M', 'Buy Me a Coffee', 'Support development'),
]

# índices de la paleta (0 transparente, 1 blanco, 15 sombra: los del copyright)
WHITE, SHADOW = 1, 15
GOLD, GOLD_DK, CYAN, QR_DARK, WHITE_MID, CYAN_MID, GOLD_MID = 2, 3, 4, 5, 6, 7, 8
COLORS = {GOLD: (248, 208, 96), GOLD_DK: (176, 128, 40), CYAN: (144, 208, 248), QR_DARK: (16, 16, 32),
          WHITE_MID: (150, 150, 165), CYAN_MID: (80, 120, 152), GOLD_MID: (150, 116, 48)}
MID = {GOLD: GOLD_MID, WHITE: WHITE_MID, CYAN: CYAN_MID}    # tono del borde suavizado de cada color


def rgb555(c):
    r, g, b = (x >> 3 for x in c)
    return 0x8000 | (b << 10) | (g << 5) | r       # bit 15 como el resto de la CLUT


# ---------- render de piezas (arrays de índices, 0 = transparente) ----------
def font_path(font):
    for d in FONT_DIRS:
        hits = sorted(glob.glob(os.path.join(d, '**', font + '.ttf'), recursive=True))
        if hits:
            return hits[0]
    sys.exit(f'falta la fuente {font}.ttf (paquete fonts-dejavu-extra, o copiarla a work/gfx/fonts/)')


def text_mask(text, font, px):
    """Texto suavizado → array 0..255 recortado a lo ancho; alto fijo por fuente y tamaño."""
    f = ImageFont.truetype(font_path(font), px)
    l, _, r, _ = f.getbbox(text)
    _, top, _, bot = f.getbbox('ñgjpqyTHbdl(')
    im = Image.new('L', (r - l + 2, bot + 2))
    ImageDraw.Draw(im).text((-l, 0), text, font=f, fill=255)
    a = np.array(im)[top:bot + 1]
    xs = np.where((a > 100).any(0))[0]
    return a[:, xs.min():xs.max() + 1]


def shadowed(a, ink):
    """Texto en dos tonos (lleno ≥ 170, borde 100–169) con sombra de 1 px abajo a la derecha (como el copyright)."""
    h, w = a.shape
    out = np.zeros((h + 1, w + 1), np.uint8)
    out[1:, 1:][a >= 100] = SHADOW
    out[:h, :w][a >= 100] = MID[ink]
    out[:h, :w][a >= 170] = ink
    return out


def wrap(text, font, px, maxw):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if cur and text_mask(t, font, px).shape[1] > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    return lines + [cur]


def balanced(text, font, px, maxw):
    """Mismo número de renglones que el ajuste ávido, pero con anchos parejos (se ve mejor centrado)."""
    n = len(wrap(text, font, px, maxw))
    words = text.split()
    best = None

    def rec(i, k, acc):
        nonlocal best
        if k == 1:
            ln = ' '.join(words[i:])
            w = text_mask(ln, font, px).shape[1]
            if w <= maxw:
                ws = [x[1] for x in acc] + [w]
                score = max(ws) - min(ws) + (0 if not acc else 0)
                if best is None or score < best[0]:
                    best = (score, [x[0] for x in acc] + [ln])
            return
        for j in range(i + 1, len(words) - k + 2):
            ln = ' '.join(words[i:j])
            w = text_mask(ln, font, px).shape[1]
            if w > maxw:
                break
            rec(j, k - 1, acc + [(ln, w)])
    rec(0, n, [])
    return best[1]


def qr_piece(data, err, scale=2, border=2):
    import segno
    q = segno.make_qr(data, error=err, boost_error=False)
    m = np.array([[bool(x) for x in row] for row in q.matrix], bool)
    n = m.shape[0] + 2 * border
    a = np.full((n, n), WHITE, np.uint8)
    a[border:border + m.shape[0], border:border + m.shape[1]][m] = QR_DARK
    return np.kron(a, np.ones((scale, scale), np.uint8)), q.version


def rule_piece(w):
    """Filete dorado: línea de 1 px con sombra, puntas más oscuras."""
    a = np.zeros((2, w), np.uint8)
    a[0, :] = GOLD
    a[0, :w // 6] = a[0, -(w // 6):] = GOLD_DK
    a[1, 1:] = SHADOW
    return a


def label_piece(l1, l2):
    """Rótulo de dos renglones centrados: nombre en blanco, explicación en celeste."""
    a = shadowed(text_mask(l1, *LABEL_FONTS[0]), WHITE)
    b = shadowed(text_mask(l2, *LABEL_FONTS[1]), CYAN)
    w = max(a.shape[1], b.shape[1])
    out = np.zeros((a.shape[0] + 1 + b.shape[0], w), np.uint8)
    out[:a.shape[0], (w - a.shape[1]) // 2:(w - a.shape[1]) // 2 + a.shape[1]] = a
    y = a.shape[0] + 1
    out[y:y + b.shape[0], (w - b.shape[1]) // 2:(w - b.shape[1]) // 2 + b.shape[1]] = b
    return out


def new_screen():
    """Las 12 piezas de la pantalla nueva con su centro en pantalla (dx, dy desde el centro 160,120)."""
    font, px = DED_FONT
    lines = DED_LINES
    pieces = []
    y = 20
    for ln in lines:
        p = shadowed(text_mask(ln, font, px), GOLD)
        pieces.append(('ded', p, y))
        y += 15
    y += 4
    pieces.append(('rule', rule_piece(150), y))
    y += 8
    head = shadowed(text_mask(HEADING, *HEAD_FONT), WHITE)
    pieces.append(('head', head, y))
    y += head.shape[0] + 5
    qrs = [qr_piece(d, e) for d, e, *_ in QRS]
    labels = [label_piece(a, b) for *_, a, b in QRS]
    gap = 136                                                  # distancia entre centros de los QR
    qh = qrs[0][0].shape[0]
    total = y + qh + 4 + max(lab.shape[0] for lab in labels) - 20
    off = (240 - total) // 2 - 20                              # todo el bloque centrado en vertical
    y += off
    out = []
    for kind, p, top in pieces:
        out.append((kind, p, 0, top + off + p.shape[0] // 2 - 120))
    for i, ((q, _), lab) in enumerate(zip(qrs, labels)):
        cx = (i * 2 - 1) * gap // 2
        out.append(('qr', q, cx, y + qh // 2 - 120))
        out.append(('label', lab, cx, y + qh + 4 + lab.shape[0] // 2 - 120))
    while len(out) < 12:                                       # la tabla tiene 12 sprites: el resto, 1 px transparente
        out.append(('pad', np.zeros((1, 1), np.uint8), 0, 0))
    return out, lines, [v for _, v in qrs]


# ---------- empaquetado ----------
ORDERS = [lambda it: (-it[1][0] * it[1][1],), lambda it: (-it[1][0], -it[1][1]), lambda it: (-it[1][1], -it[1][0]),
          lambda it: (-max(it[1]), -min(it[1]))]


def pack(items, W=256, H=240):
    """MaxRects (mejor lado corto) con varios órdenes; items = [(clave, (h, w))] → {clave: (u, v)}."""
    for order in ORDERS:
        pos = maxrects(sorted(items, key=order), W, H)
        if pos:
            return pos
    raise SystemExit(f'no entran las {len(items)} piezas en la hoja de {W}×{H}')


def maxrects(items, W, H):
    free = [(0, 0, W, H)]                                    # (x, y, w, h)
    pos = {}
    for key, (h, w) in items:
        best = None
        for fx, fy, fw, fh in free:
            if w <= fw and h <= fh:
                score = (min(fw - w, fh - h), max(fw - w, fh - h), fy, fx)
                if best is None or score < best[0]:
                    best = (score, fx, fy)
        if best is None:
            return None
        _, x, y = best
        pos[key] = (x, y)
        nf = []
        for fx, fy, fw, fh in free:                          # partir los libres que toca la pieza
            if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                nf.append((fx, fy, fw, fh))
                continue
            if x > fx:
                nf.append((fx, fy, x - fx, fh))
            if x + w < fx + fw:
                nf.append((x + w, fy, fx + fw - x - w, fh))
            if y > fy:
                nf.append((fx, fy, fw, y - fy))
            if y + h < fy + fh:
                nf.append((fx, y + h, fw, fy + fh - y - h))
        free = [a for i, a in enumerate(nf) if not any(                       # sin rectángulos contenidos en otros
            i != j and b[0] <= a[0] and b[1] <= a[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3]
            and (a != b or j < i) for j, b in enumerate(nf))]
    return pos


def layout(titledat, titl):
    t = tim.scan(titledat)[G20]
    idx = tim.indices(titledat, t)                                   # (240, 256)
    recs = copyright_patch.records(titl)
    assert len(recs) == 36, len(recs)
    crops, trim = {}, {}
    for n, o in enumerate(recs[:12]):
        f = struct.unpack_from('<16H', titl, o)
        u, v, w, h = f[8] & 255, f[8] >> 8, f[2] & 255, f[2] >> 8
        a = idx[v:v + h, u:u + w]
        ys, xs = np.where(a != 0)
        t0, l0 = ys.min(), xs.min()
        crops[n] = a[t0:ys.max() + 1, l0:xs.max() + 1].copy()
        trim[n] = (l0, t0)                                           # la tinta empieza (l0, t0) más adentro
    screen, lines, versions = new_screen()
    assert len(screen) == 12, len(screen)
    items = [(('c', n), a.shape) for n, a in crops.items()] + [(('d', n), p[1].shape) for n, p in enumerate(screen)]
    pos = pack(items)
    sheet = np.zeros_like(idx)
    for (kind, n), (u, v) in pos.items():
        a = crops[n] if kind == 'c' else screen[n][1]
        sheet[v:v + a.shape[0], u:u + a.shape[1]] = a
    return dict(t=t, sheet=sheet, crops=crops, trim=trim, screen=screen, pos=pos, recs=recs, lines=lines, versions=versions)


def clut_bytes(titledat, t):
    c = list(tim.cluts(titledat, t)[0])
    for i, col in COLORS.items():
        c[i] = rgb555(col)
    return struct.pack('<16H', *c)


def sheet_rgb(L, titledat):
    pal = list(tim.cluts(titledat, L['t'])[0])
    rgb = np.zeros((16, 3), np.uint8)
    for i, v in enumerate(pal):
        rgb[i] = [(v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3]
    for i, col in COLORS.items():
        rgb[i] = col
    return rgb


def screen_sim(L, rgb, which, bg):
    """Simula una pantalla (copyright o dedicatoria) a 320×240 sobre el fondo bg (RGB)."""
    im = bg.copy()
    if which == 'c':
        _, cop = records_new(L)
        for n, r in enumerate(cop):
            dx, dy = (x - 0x10000 if x & 0x8000 else x for x in r[1:3])
            blit(im, L['crops'][n], 160 + dx - r[4], 120 + dy - r[5], rgb)
    else:
        ded, _ = records_new(L)
        for (kind, a, _, _), r in zip(L['screen'], ded):
            dx, dy = (x - 0x10000 if x & 0x8000 else x for x in r[1:3])
            blit(im, a, 160 + dx - r[4], 120 + dy - r[5], rgb)
    return im


def blit(im, a, x0, y0, rgb):
    for (y, x), v in np.ndenumerate(a):
        if v and 0 <= y0 + y < im.shape[0] and 0 <= x0 + x < im.shape[1]:
            im[y0 + y, x0 + x] = rgb[v]


# ---------- parche ----------
FIELDS = (2, 4, 5, 8, 14, 15)       # halfwords: +4 alto<<8|ancho, +8 dx, +10 dy, +16 uv, +28 medio ancho, +30 medio alto


def records_new(L):
    """Valores (6 halfwords por sprite n) de la pantalla nueva y del copyright reempaquetado."""
    ded, cop = [], []
    for n, (kind, a, dx, dy) in enumerate(L['screen']):
        h, w = a.shape
        u, v = L['pos'][('d', n)]
        ded.append((h << 8 | w, dx & 0xFFFF, dy & 0xFFFF, v << 8 | u, (w + 1) // 2, (h + 1) // 2))
    for n, o in enumerate(L['recs'][:12]):
        f = list(struct.unpack_from('<16H', L['titl'], o))
        u, v = L['pos'][('c', n)]
        h, w = L['crops'][n].shape
        l0, t0 = L['trim'][n]                     # el ancla (medio ancho, medio alto) queda en el mismo punto de pantalla
        cop.append((h << 8 | w, f[4], f[5], v << 8 | u, f[14] - l0, f[15] - t0))
    return ded, cop


def build(titledat_in, titl_in, out):
    titledat = bytearray(open(titledat_in, 'rb').read())
    titl = bytearray(open(titl_in, 'rb').read())
    L = layout(bytes(titledat), bytes(titl))
    L['titl'] = bytes(titl)
    t = L['t']
    # hoja + paleta
    pk = L['sheet'].reshape(t['h'], -1, 2)
    titledat[t['pix_off']:t['pix_off'] + t['h'] * t['w'] // 2] = (pk[..., 0] | (pk[..., 1] << 4)).astype(np.uint8).tobytes()
    titledat[t['clut']['off']:t['clut']['off'] + 32] = clut_bytes(bytes(titledat), t)
    ded, cop = records_new(L)
    # copyright: recorte ajustado a la tinta en su nuevo lugar (las 3 tablas tienen los mismos campos)
    for i, o in enumerate(L['recs']):
        f = struct.unpack_from('<16H', titl, o)
        assert (f[4], f[5]) == cop[i % 12][1:3], (hex(o), i)
        for k, x in zip(FIELDS, cop[i % 12]):
            struct.pack_into('<H', titl, o + 2 * k, x)
    # datos para el asm
    os.makedirs(os.path.join(out, 'OVL'), exist_ok=True)
    os.makedirs(os.path.join(out, 'TITLE'), exist_ok=True)
    inc = os.path.join(out, 'dedicatoria_data.asm')
    with open(inc, 'w') as f:
        f.write('; generado por dedicatoria.py\n')
        f.write('.definelabel REC0, 0x%08X\n.definelabel REC1, 0x%08X\n.definelabel REC2, 0x%08X\n'
                % tuple(TITL_BASE + L['recs'][k] for k in (0, 12, 24)))
        for name, rows in (('ded_recs', ded), ('cop_recs', cop)):
            f.write(f'{name}:\n')
            for r in rows:
                f.write('  .halfword ' + ', '.join('0x%04X' % x for x in r) + '\n')
    titl_out = os.path.join(out, 'OVL', 'TITL_GRP.BIN')
    open(titl_out, 'wb').write(titl)
    move_in = os.path.join(WORK, 'iso_jp', 'OVL', 'MOVE_GRP.BIN')
    move_out = os.path.join(out, 'OVL', 'MOVE_GRP.BIN')
    asm = os.path.join(WORK, 'patches', 'dedicatoria.asm')
    env = dict(os.environ)
    r = subprocess.run([os.path.join(TOOLS, 'bin', 'armips'), asm, '-strequ', 'MOVE_IN', move_in,
                        '-strequ', 'MOVE_OUT', move_out, '-strequ', 'TITL_FILE', titl_out, '-strequ', 'DATA', inc,
                        '-sym', os.path.join(out, 'dedicatoria.sym')], capture_output=True, text=True, env=env)
    if r.returncode:
        sys.exit('armips: ' + r.stdout + r.stderr)
    size = os.path.getsize(move_out)
    if size > MOVE_SECTORS * 2048:
        sys.exit(f'MOVE_GRP.BIN crece a {size} B: pasa de {MOVE_SECTORS} sectores (correría los LBA de los STR)')
    open(os.path.join(out, 'TITLE', 'TITLEDAT.BIN'), 'wb').write(titledat)
    print(f'dedicatoria: {len(L["lines"])} renglones, QR v{L["versions"]}; MOVE_GRP.BIN {size} B '
          f'(libres {MOVE_SECTORS * 2048 - size}); 36 registros del copyright reubicados')


def preview(titledat_in, titl_in, png, bg_png=None):
    titledat = open(titledat_in, 'rb').read()
    titl = open(titl_in, 'rb').read()
    L = layout(titledat, titl)
    L['titl'] = titl
    rgb = sheet_rgb(L, titledat)
    bg = (np.array(Image.open(bg_png).convert('RGB').resize((320, 240))) if bg_png
          else np.full((240, 320, 3), (10, 12, 40), np.uint8))
    sheet = rgb[L['sheet']].copy()
    sheet[L['sheet'] == 0] = (60, 0, 60)
    tmp = dict(L)
    ded, cop = records_new(L)
    canvas = np.zeros((240, 256 + 16 + 640, 3), np.uint8)
    canvas[:, :256] = sheet
    canvas[:, 264:584] = screen_sim(L, rgb, 'c', bg)
    canvas[:, 592:] = screen_sim(L, rgb, 'd', bg)
    Image.fromarray(canvas).resize((canvas.shape[1] * 3, 720), Image.NEAREST).save(png)
    print('renglones:', *L['lines'], sep='\n  ')
    print('libre en la hoja:', int((L['sheet'] == 0).sum()), 'px (incluye márgenes de cada pieza)')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('build', 'preview'):
        sys.exit(__doc__)
    if sys.argv[1] == 'build':
        build(*sys.argv[2:5])
    else:
        preview(*sys.argv[2:6])
