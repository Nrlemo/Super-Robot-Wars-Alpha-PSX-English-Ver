"""Genera por script los gráficos con texto en inglés a partir de los originales japoneses (#2).

Estilos, copiados del original con los mismos índices de paleta:
  ramp     texto con antialias; cada tono se lleva al color de la paleta de brillo más parecido
           (títulos, lugares del mapa, cartel del prólogo, copyright, 第/話)
  outline  relleno muestreado renglón por renglón del japonés + contorno de 1 px
           (rótulos de interfaz, efectos y barreras; reproduce degradés y la mitad hueca de las barreras)
  solid    nítido, sin antialias: el color más claro de la paleta + sombra de 1 px (lugares del mapa)
  solid_orig  igual, pero con el más claro/oscuro de los índices del rótulo original (G19: el juego cambia la CLUT)
  shadow   nuestra fuente del juego (font/en_8px.txt) con sombra +1,+1, texto corrido en 4 páginas (prólogo)

Datos editables (versionados): work/gfx/render/Gxx.csv (una fila por caja) y work/gfx/render/prologo_en.txt.
Los títulos de escenario (G01–G13) no pasan por acá: los genera subtitle.py (#18).
Columnas del CSV: caja, x, y, w, h, jp, en, align (l/c/r), font, size, style
  en vacío = la caja queda como el japonés · en "-" = la caja queda vacía · resto = se dibuja ese texto.
  font: game8 (fuente del juego) o nombre de un .ttf (DejaVuSerif-Bold, DejaVuSans-Bold, … o uno propio en
  work/gfx/fonts/). size = tamaño máximo en px (si no entra en el ancho, se achica y después prueba la variante
  Condensed). Manual: work/gfx/MANUAL_render.md.

Uso:
  gfx_render.py init [Gxx…]        crea los CSV que falten (no pisa los existentes)
  gfx_render.py render [Gxx…]      genera work/gfx/render/out/Gxx.png + Gxx_preview.png (todas si no se indica)
Después: gfx_entrega.py check work/gfx/render/out
"""
import csv
import json
import glob
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx_entrega as G  # noqa: E402
import tim  # noqa: E402
from font_build import parse_glyphs  # noqa: E402

RENDER = os.path.join(G.WORK, 'gfx', 'render')
OUT = os.path.join(RENDER, 'out')
FONT_DIRS = [os.path.join(G.WORK, 'gfx', 'fonts'), '/usr/share/fonts', '/usr/local/share/fonts',
             os.path.expanduser('~/.local/share/fonts')]
COLS = ['caja', 'x', 'y', 'w', 'h', 'jp', 'en', 'align', 'font', 'size', 'style']
PIECE = {p['id']: p for p in G.PIECES}

# Valores por grupo: (font, size, align, style)
DEFAULTS = {'G01': ('DejaVuSerif-Bold', 20, 'c', 'ramp'), 'titulos': ('DejaVuSerif-Bold', 20, 'l', 'ramp'),
            'G18': ('DejaVuSerif-Bold', 18, 'c', 'ramp'), 'G20': ('DejaVuSans-Bold', 11, 'l', 'ramp'),
            'G19': ('game8', 8, 'c', 'outline'), 'G22': ('game8', 8, 'c', 'outline'),
            'barreras': ('game8', 8, 'l', 'outline'), 'mapa': ('DejaVuSans-Bold', 13, 'l', 'ramp')}


# Contenido de cada renglón de las hojas de títulos (leído de las imágenes): (id de misiones.csv, fragmento JP).
# Un título partido en dos renglones aparece dos veces; 'X1'/'X2' = títulos que solo existen como imagen.
T = {'X1': ('愛に時間を', 'Time for Love'), 'X2': ('サイキック・エナジー', 'Psychic Energy')}
TITLE_ROWS = {
    'G02': [[(1, '')], [(2, '')], [(3, 'ゲッターチーム')], [(3, '出撃せよ！'), (4, '')], [(5, 'シークレット・')],
            [(5, 'ナンバーズ')], [(6, '')], [(7, '')], [(8, '')], [(9, '')]],
    'G03': [[(10, '')], [(11, '')], [(12, '')], [(13, '')], [(14, '出撃！その名は')], [(14, 'ジャイアント・ロボ')],
            [(15, ''), (17, '')], [(16, '')], [(18, '')], [(19, '')]],
    'G04': [[(20, '')], [(21, '')], [(22, ''), (23, '')], [(24, '')], [(25, ''), (26, '')], [(27, '')],
            [(28, ''), (31, '紅い稲妻')], [(29, '')], [(30, '')], [(31, '空飛ぶマジンガー')]],
    'G05': [[(32, '激突！ゲッターロボ')], [(32, 'ＶＳゲッターロボＧ')], [(33, '')], [(34, ''), (35, '')], [(36, '')],
            [(37, ''), (38, '')], [(39, '獣を超え、人を超え、')], [(39, 'いでよ神の戦士')], [(40, ''), (41, '暗黒大将軍')],
            [(41, 'マジンガーＺ対')]],
    'G06': [[(42, '')], [(43, '')], [(44, '')], [(45, '')], [(46, '')], [(47, '')], [(48, 'クロスボーン・')],
            [(48, 'バンガード'), (51, '')], [(49, '')], [(50, '')]],
    'G07': [[(52, '')], [(53, '')], [(54, '')], [(55, 'トランス・'), (60, '')], [(55, 'フォーメーション')], [(57, '')],
            [(58, '')], [(59, '')], [(56, '')], [(61, '')]],
    'G08': [[(62, '')], [(63, '')], [(64, '')], [(65, '')], [(66, '')], [(67, '')], [(68, '')], [(69, '')],
            [(70, '')], [(71, '')]],
    'G09': [[(72, '')], [(73, '')], [(74, '')], [(75, ''), (79, 'ガンダム')], [(76, '')], [(77, '')], [(78, '')],
            [(79, 'ゼロと呼ばれた')], [(80, '')], [(81, '')]],
    'G10': [[(82, '')], [(83, ''), (85, '')], [(84, ''), (86, '')], [(87, ''), (89, '')],
            [(88, 'ヴァリアブル・'), (91, '')], [(88, 'フォーメーション')], [(90, '')], [(92, '')], [(93, '')], [(94, '')]],
    'G11': [[(95, ''), (98, '')], [(96, '')], [(97, '')], [(99, '')], [(100, '')], [(101, '')], [(102, '')],
            [(103, '')], [(104, '')], [(105, '')]],
    'G12': [[(106, ''), (114, '')], [(107, '')], [(108, '')], [(109, '')], [(110, '')], [(111, ''), ('X1', '')],
            [(113, '')], [(115, 'ギア・オブ・'), (112, '')], [(115, 'デスティニー'), (116, '始まる')],
            [(116, '絶望の宴は今から')]],
    'G13': [[(117, '')], [('X2', '')], [(120, ''), (122, '')], [(124, ''), (126, '')], [(125, '')], [(127, '')],
            [(128, '進路に光明、'), (129, '')], [(128, '退路に絶望'), (123, '')], [(118, '')], [(119, '')]],
}


def split_en(en, jp_full, frag, first):
    """Parte el inglés de un título partido en dos renglones, en proporción a los caracteres japoneses."""
    words = en.split(' ')
    head = len(frag) if first else len(jp_full) - len(frag)       # caracteres JP de la primera parte
    target = len(en) * head / max(len(jp_full), 1)
    k = len(words)
    if len(words) > 1:
        acc = 0
        for k, w in enumerate(words[:-1], 1):
            acc += len(w) + 1
            if acc >= target:
                break
    part = ' '.join(words[:k]) if first else ' '.join(words[k:])
    return part or '-'          # una sola palabra: la otra parte queda vacía (no japonés)


def title_rows(pid, m):
    mis = G.missions()
    seen, rows = set(), []
    for r, frags in enumerate(TITLE_ROWS[pid]):
        segs = segments(m, r * 24, r * 24 + 24, 2)
        texts = [frag or (T[tid][0] if tid in T else mis[tid]['jp']) for tid, frag in frags]
        cuts, pos = [], segs[0][0]
        for t in texts[:-1]:        # corte cerca de donde terminaría el fragmento (~23 px por carácter)
            pos += 23 * len(t)
            near = [i for i in range(1, len(segs)) if abs(segs[i][0] - pos) <= 36 and i not in cuts]
            pool = near or [i for i in range(1, len(segs)) if i not in cuts]
            cuts.append(max(pool, key=lambda i: (segs[i][0] - segs[i - 1][1], -abs(segs[i][0] - pos))))
        bounds = [0] + sorted(cuts) + [len(segs)]
        for k, (tid, frag) in enumerate(frags):
            a, b = segs[bounds[k]][0], segs[bounds[k + 1] - 1][1]
            jp, en = T[tid] if tid in T else (mis[tid]['jp'], mis[tid]['en'])
            if frag:
                en = split_en(en, jp, frag, jp.startswith(frag))
                jp = frag
            seen.add(tid)
            rows.append([f'R{r + 1:02d}{"ab"[k]}', a, r * 24, min(b - a + 2, 256 - a), 24, f'{jp} [{tid}]', en])
    return rows


def group(pid):
    n = int(pid[1:])
    return ('titulos' if 2 <= n <= 13 else 'barreras' if 23 <= n <= 32 else 'mapa' if 33 <= n <= 36
            else 'prologo' if 14 <= n <= 17 else pid)


# ---------- init: cajas iniciales ----------
def ink_mask(buf, t):
    return ~np.isin(tim.indices(buf, t), list(G.transparent(buf, t)))


def segments(m, y0, y1, gap):
    segs, s, last = [], None, -99
    for x in np.where(m[y0:y1].any(0))[0]:
        if s is None:
            s = x
        elif x - last > gap:
            segs.append((s, last + 1)); s = x
        last = x
    if s is not None:
        segs.append((s, last + 1))
    return segs


def bands(m, y0, y1):
    rows = m[y0:y1].any(1)
    out, s = [], None
    for y in range(len(rows) + 1):
        on = y < len(rows) and rows[y]
        if on and s is None:
            s = y
        if not on and s is not None:
            out.append((y0 + s, y0 + y)); s = None
    return out


def init_rows(pid):
    p = PIECE[pid]
    buf, t = G.load(p)
    m = ink_mask(buf, t)
    g = group(pid)
    rows = []
    if p.get('labels'):
        for lid, jp, x, y, w, h, en in p['labels']:
            en = en.split(' / ')[0].split(' (')[0] if lid.startswith(('L', 'E')) else en.split(' ')[0]
            rows.append([lid, x, y, w, h, jp, en])
    elif g == 'barreras':
        jp, en = next((j, e) for k, j, e in G.BARRIERS if k == p['entry'])
        rows.append(['B1', 0, 160, 80, 16, jp.split(' (')[0], en])
    elif g == 'titulos':   # caja = extensión del fragmento japonés (+2): regla conservadora hasta ubicar #18
        rows = title_rows(pid, m)
    elif g == 'mapa':
        rows.append(['H1', 164, 5, 80, 21, '現在位置', 'Location'])
        for y in range(33, 240, 16):
            for k, (a, b) in enumerate(segments(m, y, y + 16, 10)):
                rows.append([f'R{(y - 33) // 16 + 1:02d}{"abc"[k]}', a, y, min(b - a + 2, 256 - a), 16, '', ''])
    elif pid == 'G01':
        rows += [['C1', 160, 0, 24, 24, '第', '#'], ['C2', 184, 0, 24, 24, '話', '-']]
    elif pid == 'G18':
        for k, (a, b) in enumerate(bands(m, 52, 240)):
            rows.append([f'L{k + 3}', 8, a - 1, 304, b - a + 2, '', ''])
    elif pid == 'G20':
        for k, (a, b) in enumerate(bands(m, 0, 202)):
            rows.append([f'L{k + 1:02d}', 5, a, 246, b - a + 1, '', ''])
    font, size, align, style = DEFAULTS[g]
    return [r + [align, font, size, style] for r in rows]


def csv_path(pid):
    return os.path.join(RENDER, f'{pid}.csv')


def init(ids):
    os.makedirs(RENDER, exist_ok=True)
    for pid in ids:
        if group(pid) == 'prologo' or pid in ('G21', 'G37') or os.path.exists(csv_path(pid)):
            continue
        with open(csv_path(pid), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(COLS)
            w.writerows(init_rows(pid))
        print('creado', os.path.relpath(csv_path(pid), G.WORK))
    tp = os.path.join(RENDER, 'prologo_en.txt')
    if not os.path.exists(tp):
        open(tp, 'w', encoding='utf-8').write(
            '# Prólogo en inglés (G14–G17). Una línea en blanco = párrafo nuevo. Las líneas que empiezan con #\n'
            '# se ignoran. El corte de renglón lo hace el script (238 px); entran 84 renglones en total (sin blancos: el párrafo nuevo lo marca la pausa).\n\n')
        print('creado', os.path.relpath(tp, G.WORK))


# ---------- fuentes ----------
_game = None


# Dígitos para gráficos: los de 8FONT_R.TIM son de otro estilo (huecos, 10 px) y en en_8px.txt están como
# "keep". Estos siguen la grilla de las mayúsculas de en_8px (4 px de ancho, filas 1–8).
DIGITS = {'0': '.##.|#..#|#..#|#.##|##.#|#..#|#..#|.##.', '1': '.#.|##.|.#.|.#.|.#.|.#.|.#.|###',
          '2': '.##.|#..#|...#|..#.|.#..|#...|#...|####', '3': '###.|...#|...#|.##.|...#|...#|...#|###.',
          '4': '..#.|.##.|#.#.|#.#.|####|..#.|..#.|..#.', '5': '####|#...|#...|###.|...#|...#|#..#|.##.',
          '6': '.##.|#...|#...|###.|#..#|#..#|#..#|.##.', '7': '####|...#|..#.|..#.|.#..|.#..|.#..|.#..',
          '8': '.##.|#..#|#..#|.##.|#..#|#..#|#..#|.##.', '9': '.##.|#..#|#..#|#..#|.###|...#|...#|.##.'}


def game_glyphs():
    """{código: (máscara bool 11×w, avance)}: en_8px.txt + DIGITS para los glifos "keep"."""
    global _game
    if _game is None:
        raw = parse_glyphs(Path(G.WORK) / 'font' / 'en_8px.txt')
        _game = {}
        for ch, pat in DIGITS.items():
            rows = pat.split('|')
            a = np.zeros((11, len(rows[0])), bool)
            a[1:9] = [[c == '#' for c in r] for r in rows]
            _game[ord(ch)] = (a, a.shape[1] + 1)
        for code, (rows, adv) in raw.items():
            if adv == 'keep':
                if code not in _game:
                    _game[code] = (np.zeros((11, 3), bool), 4)
            else:
                w = max(len(x) for x in rows)
                a = np.array([[ch == '#' for ch in x.ljust(w, '.')] for x in rows], bool).reshape(len(rows), w)
                _game[code] = (a, adv if adv is not None else w + 1)
    return _game


def game_mask(text, track=0):
    """Máscara del texto con la fuente del juego: alto 11 (fila 8 = línea de base), avance VWF."""
    gl = game_glyphs()
    cells = [gl.get(0xA0 if ch == ' ' else ord(ch), gl[ord('?')]) for ch in text]
    out = np.zeros((11, max(sum(adv + track for _, adv in cells), 1)), bool)
    x = 0
    for a, adv in cells:
        out[:a.shape[0], x:x + a.shape[1]] |= a
        x += adv + track
    return out


def find_font(name):
    if os.path.isfile(name):
        return name
    for d in FONT_DIRS:
        hits = glob.glob(os.path.join(d, '**', name + '.[ot]tf'), recursive=True)
        if hits:
            return hits[0]
    return None


def ttf_render(text, path, px, aa, tight=False):
    """Texto → array (float 0..1 si aa, bool si no); alto fijo por tamaño (misma línea de base para todo texto).
    tight: sin el lugar de los acentos de mayúscula (renglones apilados más juntos; el inglés no los usa)."""
    f = ImageFont.truetype(path, px)
    l, _, r, _ = f.getbbox(text)
    _, rt, _, rb = f.getbbox('bdfhklgjpqyTH' if tight else 'ÀÉgjpqyTH|')
    im = Image.new('L', (max(r - l, 1) + 2, rb + 2))
    d = ImageDraw.Draw(im)
    d.fontmode = 'L' if aa else '1'
    d.text((1 - l, 0), text, font=f, fill=255)
    a = np.array(im)[rt:rb + 1]
    xs = np.where(a.any(0))[0]
    a = a[:, xs.min():xs.max() + 1] if len(xs) else a
    return a / 255.0 if aa else a > 127


def fit(text, font, size, w, h, aa, track=0):
    """Prueba de size para abajo (y la variante Condensed) hasta que entre en w×h. Devuelve (array, entra)."""
    if font == 'game8':    # con espaciado extra si entra (más legible con contorno); si no, sin espaciado
        for tr in sorted({track, 0}, reverse=True):
            m = game_mask(text, tr)
            if m.shape[0] > h:
                ys = np.where(m.any(1))[0]
                m = m[ys.min():ys.max() + 1] if len(ys) else m
            if m.shape[1] <= w and m.shape[0] <= h:
                return m, True
        return m, False
    names = [font] + ([font.replace('-', 'Condensed-', 1)] if 'Condensed' not in font else [])
    paths = []
    for name in names:
        path = find_font(name)
        if path is None:
            if name == font:
                raise SystemExit(f'fuente no encontrada: {font} (poné el .ttf en work/gfx/fonts/)')
            continue
        paths.append(path)
    best = None
    if '|' not in text:
        sizes = range(int(size), max(7, int(size * 0.6)) - 1, -1)
        # sin antialias (lugares del mapa): a cada tamaño, la Condensed antes de achicar (2 px menos se lee peor)
        order = [(px, p) for px in sizes for p in paths] if not aa else [(px, p) for p in paths for px in sizes]
        for px, path in order:
            best = ttf_render(text, path, px, aa)
            if best.shape[1] <= w and best.shape[0] <= h:
                return best, True
    # dos renglones: corte forzado con "|" o el más parejo; el tamaño más grande que entre en w×h
    words = text.replace('|', ' | ').split()
    cuts = [words.index('|')] if '|' in words else range(1, len(words))
    words = [x for x in words if x != '|']
    if len(words) < 2:
        return best, False
    for path in paths:
        for px in range(int(size * 0.6), 8, -1):
            cand = []
            for k in cuts:
                a, b = (ttf_render(' '.join(p), path, px, aa, tight=True) for p in (words[:k], words[k:]))
                ww = max(a.shape[1], b.shape[1])
                if ww <= w and a.shape[0] + b.shape[0] <= h:
                    cand.append((ww, a, b))
            if cand:
                _, a, b = min(cand, key=lambda c: c[0])
                out = np.zeros((a.shape[0] + b.shape[0], max(a.shape[1], b.shape[1])), a.dtype)
                out[:a.shape[0], :a.shape[1]] = a
                out[a.shape[0]:, :b.shape[1]] = b
                return out, True
    return best, False


# ---------- estilos ----------
def box_bg(orig, box, tr):
    """Fondo de la caja: transparente, salvo que el borde de la caja sea opaco (iconos con fondo)."""
    x, y, w, h = box
    sub = orig[y:y + h, x:x + w]
    ring = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]).tolist()
    v, n = Counter(ring).most_common(1)[0]
    return v if n > len(ring) * 0.6 else min(tr)


def sample_outline(orig, box, bgset, lum):
    """Del japonés en la caja: índice de contorno y relleno por renglón (None = renglón hueco)."""
    x, y, w, h = box
    sub = orig[y:y + h, x:x + w]
    ink = ~np.isin(sub, list(bgset))
    pad = np.pad(ink, 1)
    inner = ink & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    edge = ink & ~inner
    top2 = [v for v, _ in Counter(sub[edge].tolist()).most_common(2)] if edge.any() else [1]
    outline = min(top2, key=lambda v: lum[v])   # el contorno es el más oscuro de los dos más comunes del borde
    fills = []
    for r in range(h):
        if not ink[r].any():
            continue
        c = Counter(sub[r][inner[r]].tolist()) or Counter(v for v in sub[r][ink[r]].tolist() if v != outline)
        fills.append(c.most_common(1)[0][0] if c else None)
    return outline, fills or [outline]


def draw_outline(idx, m, x, y, outline, fills):
    H, W = idx.shape
    pad = np.pad(m, 1)
    dil = np.zeros_like(pad)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            dil |= np.roll(np.roll(pad, dy, 0), dx, 1)
    for (yy, xx), v in np.ndenumerate(dil):
        if v and 0 <= y + yy - 1 < H and 0 <= x + xx - 1 < W:
            idx[y + yy - 1, x + xx - 1] = outline
    for (yy, xx), v in np.ndenumerate(m):
        if v and y + yy < H and x + xx < W:
            f = fills[yy * (len(fills) - 1) // max(m.shape[0] - 1, 1)]
            idx[y + yy, x + xx] = outline if f is None else f


def palette_lum(buf, t):
    rgb = tim.bgr555(tim.cluts(buf, t)[0])[:, :3].astype(float)
    return rgb @ [0.299, 0.587, 0.114]


def draw_ramp(idx, a, x, y, buf, t, bgset):
    lum = palette_lum(buf, t)
    cand = [i for i in range(len(lum)) if i not in bgset]
    top = max(lum[i] for i in cand)
    H, W = idx.shape
    for (yy, xx), v in np.ndenumerate(a):
        if v >= 0.15 and y + yy < H and x + xx < W:
            idx[y + yy, x + xx] = min(cand, key=lambda i: abs(lum[i] - v * top))


def draw_shadow(idx, m, x, y, ink=1, shadow=3):
    H, W = idx.shape
    for (yy, xx), v in np.ndenumerate(m):
        if v and y + yy + 1 < H and x + xx + 1 < W:
            idx[y + yy + 1, x + xx + 1] = shadow
    for (yy, xx), v in np.ndenumerate(m):
        if v and y + yy < H and x + xx < W:
            idx[y + yy, x + xx] = ink


# ---------- render ----------
def place(a, box, align):
    x, y, w, h = box
    dx = {'l': 0, 'c': (w - a.shape[1]) // 2, 'r': w - a.shape[1]}.get(align, 0)
    return x + max(dx, 0), y + max((h - a.shape[0]) // 2, 0)


def render_boxes(pid):
    p = PIECE[pid]
    buf, t = G.load(p)
    orig = tim.indices(buf, t)
    idx = orig.copy()
    tr = G.transparent(buf, t)
    problems = []
    for r in csv.DictReader(open(csv_path(pid), encoding='utf-8')):
        en = r['en']
        if not en:
            continue
        box = tuple(int(r[k]) for k in ('x', 'y', 'w', 'h'))
        x, y, w, h = box
        bg = box_bg(orig, box, tr)
        work = idx.copy()
        work[y:y + h, x:x + w] = bg
        if en != '-':
            outline_style = r['style'] == 'outline'
            solid_style = r['style'] in ('solid', 'solid_orig')   # nítido: sin antialias, color más claro + sombra de 1 px
            room = (w - 2, h - 2) if outline_style else (w - 1, h - 1) if solid_style else (w, h)
            a, ok = fit(en, r["font"], float(r["size"]), room[0], room[1], not (outline_style or solid_style),
                        1 if outline_style else 0)
            if not ok:
                problems.append(f"{pid} {r['caja']}: \"{en}\" no entra en {w}×{h} (mide {a.shape[1]}×{a.shape[0]})")
            if outline_style:
                outline, fills = sample_outline(orig, box, tr | {bg}, palette_lum(buf, t))
                px, py = place(a, (x + 1, y + 1, w - 2, h - 2), r['align'])
                draw_outline(work, a.astype(bool), px, py, outline, fills)
            elif solid_style:
                lum = palette_lum(buf, t)
                cand = [i for i in range(len(lum)) if i not in (tr | {bg})]
                if r['style'] == 'solid_orig':   # solo los índices del rótulo original: el juego le cambia la CLUT
                    c = Counter(v for v in orig[y:y + h, x:x + w].ravel().tolist() if v in cand)
                    n = sum(c.values())
                    cand = [i for i, k in c.items() if k * 10 >= n] or cand
                ink, shadow = max(cand, key=lambda i: lum[i]), min(cand, key=lambda i: lum[i])
                px, py = place(a, (x, y, w - 1, h - 1), r['align'])
                draw_shadow(work, a.astype(bool), px, py, ink, shadow)
            else:
                px, py = place(a, box, r['align'])
                draw_ramp(work, a, px, py, buf, t, tr | {bg})
        keep = [int(v, 16) for v in (r.get('conservar') or '').split()]   # índices del arte que no son texto
        if keep:
            sub = orig[y:y + h, x:x + w]
            work[y:y + h, x:x + w][np.isin(sub, keep)] = sub[np.isin(sub, keep)]
        idx[y:y + h, x:x + w] = work[y:y + h, x:x + w]   # nada sale de la caja
    return p, buf, t, idx, problems


def prologue_lines():
    txt = os.path.join(RENDER, 'prologo_en.txt')
    if not os.path.exists(txt):
        return []
    paras, cur = [], []
    for line in open(txt, encoding='utf-8'):
        if line.startswith('#'):
            continue
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(' '.join(cur)); cur = []
    if cur:
        paras.append(' '.join(cur))
    out = []                        # (renglón, último del párrafo): sin renglones en blanco, como el japonés
    for para in paras:
        line = ''
        for word in para.split(' '):
            cand = f'{line} {word}' if line else word
            if game_mask(cand).shape[1] <= 238:
                line = cand
            else:
                out.append((line, False)); line = word
        out.append((line, True))
    return out


def render_prologue():
    """4 páginas de 21 renglones + tabla de pausas de PRO_GRP (G.PRO_TABLE): el juego saca un renglón cada 40
    cuadros, 80 al cerrar un párrafo (deja el hueco de un renglón), y termina en -1."""
    out = prologue_lines()
    if not out:
        return [], ['prólogo: prologo_en.txt vacío (no se genera)']
    cap = min(84, G.PRO_TABLE_MAX)
    problems = [] if len(out) <= cap else [f'prólogo: {len(out)} renglones > {cap} (sobran {len(out) - cap})']
    res = []
    for k, pid in enumerate(('G14', 'G15', 'G16', 'G17')):
        p = PIECE[pid]
        buf, t = G.load(p)
        idx = tim.indices(buf, t).copy()
        idx[0:252, 0:240] = 0
        for j, (line, _) in enumerate(out[k * 21:(k + 1) * 21]):
            if line:
                draw_shadow(idx, game_mask(line), 1, j * 12)
        res.append((p, buf, t, idx))
    delays = [80 if end else 40 for _, end in out[:cap]]
    delays[-1] = 40                 # el japonés termina en 40 antes del -1
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, G.PRO_TABLE), 'w', encoding='utf-8') as f:
        json.dump(delays, f)
    return res, problems


def save(p, buf, t, idx):
    os.makedirs(OUT, exist_ok=True)
    cl = tim.cluts(buf, t)
    tim.save_png(tim.indexed_png(idx, cl[0]), os.path.join(OUT, p['id'] + '.png'))
    a = Image.fromarray(tim.bgr555(cl[0][tim.indices(buf, t)]), 'RGBA')
    b = Image.fromarray(tim.bgr555(cl[0][idx]), 'RGBA')
    s = 3 if t['w'] <= 256 else 2
    pv = Image.new('RGBA', (t['w'] * 2 + 4, t['h']), (60, 60, 70, 255))
    pv.alpha_composite(a, (0, 0))
    pv.alpha_composite(b, (t['w'] + 4, 0))
    pv.resize((pv.width * s, pv.height * s), Image.NEAREST).save(os.path.join(OUT, p['id'] + '_preview.png'))


def boxes_image(pid, buf, t):
    """Original ×3 con cada caja del CSV numerada: para saber qué fila del CSV es cada texto."""
    im = Image.fromarray(tim.bgr555(tim.cluts(buf, t)[0][tim.indices(buf, t)]), 'RGBA')
    bg = Image.new('RGBA', im.size, (60, 60, 70, 255))
    bg.alpha_composite(im)
    s = 3 if t['w'] <= 256 else 2
    bg = bg.resize((t['w'] * s, t['h'] * s), Image.NEAREST)
    d = ImageDraw.Draw(bg)
    for r in csv.DictReader(open(csv_path(pid), encoding='utf-8')):
        x, y, w, h = (int(r[k]) for k in ('x', 'y', 'w', 'h'))
        d.rectangle([x * s, y * s, (x + w) * s - 1, (y + h) * s - 1], outline=(0, 255, 0, 255))
        d.text((x * s + 2, (y + h) * s - 11), r['caja'], fill=(255, 255, 0, 255))
    bg.save(os.path.join(OUT, pid + '_cajas.png'))


def render(ids):
    problems = []
    for pid in ids:
        if pid == 'G37':   # rótulos del mapa: kief_labels.py (copias/bandas de la hoja de KIEFETIM.BIN)
            import kief_labels
            problems += kief_labels.render()
            continue
        if pid in ('G33', 'G34', 'G35', 'G36'):   # lugares del mapa: mapa_lugares.py reempaqueta las cuatro hojas (#188)
            if pid == next(i for i in ids if i in ('G33', 'G34', 'G35', 'G36')):
                import mapa_lugares
                problems += mapa_lugares.render()
            continue
        if group(pid) != 'prologo' and os.path.exists(csv_path(pid)):
            p, buf, t, idx, pr = render_boxes(pid)
            save(p, buf, t, idx)
            boxes_image(pid, buf, t)
            problems += pr
            print('generado', pid)
    if any(group(i) == 'prologo' for i in ids):
        res, pr = render_prologue()
        for p, buf, t, idx in res:
            save(p, buf, t, idx)
            print('generado', p['id'])
        problems += pr
    for x in problems:
        print('AVISO', x)
    print(f'→ {os.path.relpath(OUT, G.REPO)}/  ·  validar: gfx_entrega.py check {os.path.relpath(OUT, G.REPO)}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    # G01–G13 (títulos de escenario) los genera subtitle.py con la tabla de recortes del juego (#18)
    ids = sys.argv[2:] or [p['id'] for p in G.PIECES if p['id'] != 'G21' and not 1 <= int(p['id'][1:]) <= 13]
    if any(1 <= int(i[1:]) <= 13 for i in ids):
        sys.exit('G01–G13: los títulos de escenario los genera subtitle.py (work/gfx/MANUAL_render.md)')
    if cmd == 'init':
        init(ids)
    elif cmd == 'render':
        render(ids)
    else:
        print(__doc__)
