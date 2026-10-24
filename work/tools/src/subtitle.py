"""Títulos de escenario en inglés (#18): hojas de TITLE/SUBTITLE.BIN + tabla de recortes del overlay SNMP.

Formato (descifrado del código de SNMP, rutina 0x800D7460; ver notes/graficos.md):
- SUBTITLE.BIN: el juego lee con offsets fijos: 0x800 fondo (TIM 8 bpp), 0x13620 celdas `0–9 第 話` (TIM #1, VRAM
  576,384) y la hoja del título en 0x14020 + hoja·0x8040 (TIM 4 bpp 256×256, siempre a VRAM 832,256). La cabecera
  (u32 offsets) no se usa. Las hojas se pueden agregar al final (el archivo crece; el juego busca por nombre).
- SNMP (enlazado en 0x800D61D8): PIECES 0x800FD180 = 144 registros de 8 B `u8 u, u8 v, u16 ancho, u16 x, u16 y`
  (alto fijo 24; x/y en pantalla de 320×240); COUNTS 0x800FD600 = u8 pedazos por título; SHEETS 0x800FD684 = u8 hoja.
  Índice = id de misiones.csv − 1; los pedazos de un título van seguidos, a partir de la suma de los anteriores.
  Todos los pedazos de un título tienen que estar en la misma hoja. El total no puede pasar de 144.
- Encabezado 第N話 (y=40): sprites de 24 px (第 u=160, 話 u=184) y dígitos de 16 px (u = 16·dígito); las x son
  inmediatos del código. En inglés: "Stage" dibujado sobre las dos celdas (48 px contiguos en la textura) y 話 movido
  al lado de 第, antes de los dígitos (STAGE_PATCH): `Stage 7` / `Stage 12`, centrado como el japonés.

Texto: el `en` de traduccion/referencia/misiones.csv (el mismo del menú de intermisión); work/gfx/render/titulos.csv
puede reemplazarlo por título (columna `en`; `|` = corte de renglón en pantalla).

Uso:
  subtitle.py dump                          tabla japonesa (CSV a stdout)
  subtitle.py build <SNMP_GRP.BIN|-> <dir>  dir/SUBTITLE.BIN + dir/SNMP_GRP.BIN (+ preview/ y titulos.csv de informe)
                                            ('-' = SNMP de iso_jp; en el pipeline, la salida de "entry")
  subtitle.py selftest                      tabla japonesa leída y reescrita == original
"""
import csv
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tim  # noqa: E402

WORK = tim.WORK
REPO = os.path.dirname(WORK)
SUB = os.path.join(tim.ISO, 'TITLE', 'SUBTITLE.BIN')
SNMP = os.path.join(tim.ISO, 'OVL', 'SNMP_GRP.BIN')
MISIONES = os.path.join(REPO, 'traduccion', 'referencia', 'misiones.csv')
OVERRIDES = os.path.join(WORK, 'gfx', 'render', 'titulos.csv')

BASE = 0x800D61D8                      # dirección de enlace de SNMP_GRP.BIN
PIECES, COUNTS, SHEETS = 0x800FD180, 0x800FD600, 0x800FD684
MAX_PIECES, N_TITLES = 144, 132
SHEET0, SHEET_SIZE, ROW_H, ROWS = 0x14020, 0x8040, 24, 10     # 10 renglones de 24 px por hoja (sobran 16 px)
SCREEN_W, MAX_LINE = 320, 304                                 # ancho de un renglón en pantalla (margen 8 px)
LINE_Y = {1: [104], 2: [93, 120]}                             # y de los renglones, como en el japonés

FONT, SIZE = 'LiberationSerif-Bold', 20
FONT_DIRS = ['/usr/share/fonts', os.path.join(WORK, 'gfx', 'fonts'), os.path.expanduser('~/.local/share/fonts')]

STAGE_WORD = 'Stage'
STAGE_CELL = (160, 48)                 # x y ancho de 第+話 en el TIM #1
STAGE_GAP = 5                          # espacio entre "Stage" y el primer dígito
# (dirección, instrucción japonesa, instrucción nueva): x de 話 y de los dígitos en el encabezado
STAGE_PATCH = [
    (0x800D7A0C, 0x240400B0, 0x24040090),   # 2 dígitos: 話 176 → 144 (a la derecha de 第 en 120)
    (0x800D7A18, 0x240400A8, 0x24040098),   # 1 dígito:  話 168 → 152 (a la derecha de 第 en 128)
    (0x800D7AC8, 0x24420090, 0x244200A8),   # decenas 144 → 168
    (0x800D7B54, 0x24050098, 0x240500B0),   # unidades (1 dígito) 152 → 176
    (0x800D7B58, 0x240500A0, 0x240500B8),   # unidades (2 dígitos) 160 → 184
]
STAGE_Y = 0x800D7A2C                   # addiu v1, v1, 0x28: y de 第/話 (40); baja si la "g" no entra en la celda
STAGE_Y_JP = 0x24630028


# ---------- tabla ----------
def read_table(snmp):
    counts = snmp[COUNTS - BASE:COUNTS - BASE + N_TITLES]
    sheets = snmp[SHEETS - BASE:SHEETS - BASE + N_TITLES]
    out, k = [], 0
    for t in range(N_TITLES):
        parts = [struct.unpack_from('<BBHHH', snmp, PIECES - BASE + 8 * (k + j)) for j in range(counts[t])]
        k += counts[t]
        out.append((sheets[t], parts))
    return out


def write_table(snmp, table):
    d = bytearray(snmp)
    recs = [p for _, parts in table for p in parts]
    if len(recs) > MAX_PIECES:
        raise SystemExit(f'ERROR: {len(recs)} pedazos; la tabla admite {MAX_PIECES}')
    blob = b''.join(struct.pack('<BBHHH', *p) for p in recs)
    old = d[PIECES - BASE:PIECES - BASE + 8 * MAX_PIECES]
    d[PIECES - BASE:PIECES - BASE + 8 * MAX_PIECES] = blob + old[len(blob):]
    d[COUNTS - BASE:COUNTS - BASE + N_TITLES] = bytes(len(parts) for _, parts in table)
    d[SHEETS - BASE:SHEETS - BASE + N_TITLES] = bytes(s for s, _ in table)
    return bytes(d)


def patch_code(snmp, patches):
    d = bytearray(snmp)
    for addr, old, new in patches:
        cur = struct.unpack_from('<I', d, addr - BASE)[0]
        if cur not in (old, new):
            raise SystemExit(f'ERROR: {addr:#x} = {cur:#010x}, se esperaba {old:#010x} (¿otro SNMP?)')
        struct.pack_into('<I', d, addr - BASE, new)
    return bytes(d)


# ---------- texto ----------
def titles():
    mis = {int(r['titulo_id']): r for r in csv.DictReader(open(MISIONES, encoding='utf-8'))}
    over = {}
    if os.path.isfile(OVERRIDES):
        over = {int(r['id']): r['en'] for r in csv.DictReader(open(OVERRIDES, encoding='utf-8')) if r['en'].strip()}
    return {t: (mis[t]['jp'], over.get(t, mis[t]['en'])) for t in mis}


def find_font(name):
    for d in FONT_DIRS:
        for root, _, files in os.walk(d):
            for ext in ('.ttf', '.otf'):
                if name + ext in files:
                    return os.path.join(root, name + ext)
    raise SystemExit(f'fuente no encontrada: {name} (poné el .ttf en work/gfx/fonts/)')


class Renderer:
    """Texto → array float 0..1 de 24 px de alto; misma línea de base para todo (centrado entre H y gjpqy)."""

    def __init__(self, name=FONT, px=SIZE):
        self.f = ImageFont.truetype(find_font(name), px)
        top = self.f.getbbox('H|')[1]
        bot = self.f.getbbox('gjpqy|')[3]
        self.y0 = (ROW_H - (bot - top)) // 2 - top

    def __call__(self, text):
        l, t, r, b = self.f.getbbox(text)
        im = Image.new('L', (r - l + 4, ROW_H))
        ImageDraw.Draw(im).text((2 - l, self.y0), text, font=self.f, fill=255)
        a = np.array(im) / 255.0
        clipped = t + self.y0 < 0 or b + self.y0 > ROW_H
        xs = np.where((a >= 0.15).any(0))[0]
        return a[:, xs.min():xs.max() + 1], clipped

    def width(self, text):
        return self(text)[0].shape[1]


def break_lines(text, r):
    """Un renglón si entra en pantalla; si no, el corte entre palabras más parejo (premia cortar tras , : ! ?)."""
    if '|' in text:
        return [s.strip() for s in text.split('|')]
    if r.width(text) <= MAX_LINE:
        return [text]
    words = text.split(' ')
    best = None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]), ' '.join(words[k:])
        cost = max(r.width(a), r.width(b)) - (40 if words[k - 1][-1] in ',:!?.' else 0)
        if best is None or cost < best[0]:
            best = (cost, [a, b])
    return best[1]


def stage_word(digits_idx):
    """STAGE_WORD con la línea de base de los dígitos japoneses (última fila con tinta de las celdas 0–9), en el
    mayor tamaño ≤ SIZE que entre en las celdas 第+話 dejando STAGE_GAP px antes del primer dígito. Si los trazos
    de abajo (g) no entran en los 24 px, el texto sube `shift` px en la celda y el sprite baja lo mismo en pantalla
    (STAGE_Y) → misma base que los dígitos. Devuelve (array, shift)."""
    base = int(np.where((digits_idx[:, :160] > 0).any(1))[0].max()) + 1      # fila de la línea de base
    for px in range(SIZE, 11, -1):
        f = ImageFont.truetype(find_font(FONT), px)
        im = Image.new('L', (STAGE_CELL[1] * 2, 3 * ROW_H))
        ImageDraw.Draw(im).text((4, ROW_H + base), STAGE_WORD, font=f, fill=255, anchor='ls')
        a = np.array(im) / 255.0
        xs = np.where((a >= 0.15).any(0))[0]
        ys = np.where((a >= 0.15).any(1))[0]
        if xs.max() - xs.min() + 1 > STAGE_CELL[1] - STAGE_GAP:
            continue
        shift = max(0, int(ys.max()) - (2 * ROW_H - 1))                    # filas que se salen por abajo
        if ys.min() - shift < ROW_H:
            raise SystemExit(f'ERROR: "{STAGE_WORD}" no entra en el alto de la celda')
        return a[ROW_H + shift:2 * ROW_H + shift, xs.min():xs.max() + 1], shift
    raise SystemExit(f'ERROR: "{STAGE_WORD}" no entra en las celdas 第+話 ({STAGE_CELL[1]} px)')


def split_piece(a):
    """Un renglón de más de 256 px → dos pedazos, cortando por la columna con menos tinta cerca de la mitad."""
    if a.shape[1] <= 256:
        return [a]
    mid, ink = a.shape[1] // 2, a.sum(0)
    lo, hi = max(a.shape[1] - 256, mid - 24), min(256, mid + 24)
    cut = lo + int(np.argmin(ink[lo:hi + 1]))
    return [a[:, :cut], a[:, cut:]]


# ---------- empaquetado ----------
def pack(items):
    """items: {id: [anchos]} → {id: (hoja, [(u, renglón)])}; todos los pedazos de un título en la misma hoja.
    Mejor ajuste por renglón, títulos de mayor a menor."""
    sheets, place = [], {}
    order = sorted(items, key=lambda t: (-max(items[t]), -sum(items[t]), t))
    for t in order:
        for s, free in enumerate(sheets + [[256] * ROWS]):
            trial, spots = list(free), []
            for w in sorted(items[t], reverse=True):
                fits = [r for r in range(ROWS) if trial[r] >= w]
                if not fits:
                    break
                r = min(fits, key=lambda r: (trial[r], r))
                spots.append((w, 256 - trial[r], r))
                trial[r] -= w
            else:
                if s == len(sheets):
                    sheets.append(trial)
                else:
                    sheets[s] = trial
                # devolver en el orden original de los pedazos
                pool = sorted(spots, reverse=True)
                out = []
                for w in items[t]:
                    i = next(i for i, sp in enumerate(pool) if sp[0] == w)
                    out.append(pool.pop(i)[1:])
                place[t] = (s, out)
                break
    return place, len(sheets)


# ---------- dibujo ----------
def ramp(buf, t, a):
    """Tonos 0..1 → índices de la paleta del TIM por brillo (como gfx_render: estilo 'ramp'); 0 = transparente."""
    rgb = tim.bgr555(tim.cluts(buf, t)[0])
    lum = rgb[:, :3].astype(float) @ [0.299, 0.587, 0.114]
    cand = np.array([i for i in range(len(lum)) if rgb[i, 3]])
    top = lum[cand].max()
    near = cand[np.abs(lum[cand][None, :] - (a.reshape(-1, 1) * top)).argmin(1)].reshape(a.shape)
    return np.where(a >= 0.15, near, 0).astype(np.uint8)


def put_pixels(buf, t, idx):
    b = bytearray(buf)
    p = idx.reshape(t['h'], -1, 2)
    b[t['pix_off']:t['pix_off'] + t['vram_w'] * 2 * t['h']] = (p[..., 0] | (p[..., 1] << 4)).astype(np.uint8).tobytes()
    return bytes(b)


def build(snmp_in, outdir):
    snmp = open(snmp_in if snmp_in != '-' else SNMP, 'rb').read()
    sub = open(SUB, 'rb').read()
    jp_table = read_table(snmp)
    r = Renderer()
    txt = titles()
    lay, problems = {}, []
    for t in range(1, N_TITLES + 1):
        if not jp_table[t - 1][1]:                     # sin imagen (欠番, 130–132)
            continue
        jp, en = txt[t]
        lines = break_lines(en, r)
        if len(lines) > 2:
            raise SystemExit(f'ERROR: título {t}: más de 2 renglones')
        arrs = []
        for ln in lines:
            a, clipped = r(ln)
            if clipped:
                problems.append(f'título {t}: "{ln}" se sale del alto de 24 px')
            if a.shape[1] > MAX_LINE:
                problems.append(f'título {t}: "{ln}" mide {a.shape[1]} px (máx. {MAX_LINE}); cortar con | en titulos.csv')
            arrs.append(a)
        lay[t] = (jp, en, lines, arrs, [split_piece(a) for a in arrs])
    items = {t: [p.shape[1] for pcs in v[4] for p in pcs] for t, v in lay.items()}
    total = sum(len(v) for v in items.values())
    if total > MAX_PIECES:
        raise SystemExit(f'ERROR: {total} pedazos > {MAX_PIECES}: acortar o partir distinto los títulos más largos')
    place, nsheets = pack(items)

    ts = tim.scan(sub)
    sheet_t = ts[2:]
    out = bytearray(sub)
    for s in range(len(sheet_t), nsheets):             # hojas nuevas al final (copia de la última, misma paleta)
        last = sheet_t[-1]
        out += sub[last['off']:last['off'] + SHEET_SIZE]
    ts_out = tim.scan(bytes(out))
    for k, t in enumerate(ts_out):                     # cabecera de offsets (el juego no la usa)
        struct.pack_into('<I', out, 4 * k, t['off'])
    assert all(t['off'] == SHEET0 + k * SHEET_SIZE for k, t in enumerate(ts_out[2:]))
    canvases = [np.zeros((256, 256), np.uint8) for _ in range(max(nsheets, len(sheet_t)))]
    table = [(jp_table[t - 1][0], []) for t in range(1, N_TITLES + 1)]   # sin imagen: igual que el japonés
    report = []
    for t, (jp, en, lines, arrs, pcs) in lay.items():
        s, spots = place[t]
        tbuf, tt = bytes(out), ts_out[2 + s]
        parts, i = [], 0
        for ln, (a, pieces) in enumerate(zip(arrs, pcs)):
            x = (SCREEN_W - a.shape[1]) // 2
            y = LINE_Y[len(lines)][ln]
            for p in pieces:
                u, row = spots[i]
                i += 1
                canvases[s][row * ROW_H:(row + 1) * ROW_H, u:u + p.shape[1]] = ramp(tbuf, tt, p)
                parts.append((u, row * ROW_H, p.shape[1], x, y))
                x += p.shape[1]
        table[t - 1] = (s, parts)
        report.append(dict(id=t, jp=jp, en=' | '.join(lines), hoja=s, pedazos=len(parts),
                           ancho=max(a.shape[1] for a in arrs),
                           recortes=' '.join(f'{u},{v},{w}@{x},{y}' for u, v, w, x, y in parts)))
    for s, t in enumerate(ts_out[2:]):
        out[:] = put_pixels(bytes(out), t, canvases[s])

    # encabezado "Stage": celdas 第+話 del TIM #1, con la línea de base de los dígitos y pegado a ellos
    t1 = ts_out[1]
    idx = tim.indices(bytes(out), t1).copy()
    a, shift = stage_word(idx)
    cx, cw = STAGE_CELL
    idx[:, cx:cx + cw] = 0
    x0 = cx + cw - STAGE_GAP - a.shape[1]
    idx[:, x0:x0 + a.shape[1]] = ramp(bytes(out), t1, a)
    out[:] = put_pixels(bytes(out), t1, idx)

    snmp_out = patch_code(write_table(snmp, table), STAGE_PATCH + [(STAGE_Y, STAGE_Y_JP, STAGE_Y_JP + shift)])
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'SUBTITLE.BIN'), 'wb').write(out)
    open(os.path.join(outdir, 'SNMP_GRP.BIN'), 'wb').write(snmp_out)
    with open(os.path.join(outdir, 'titulos.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, list(report[0]))
        w.writeheader()
        w.writerows(sorted(report, key=lambda x: x['id']))
    preview(bytes(out), snmp_out, os.path.join(outdir, 'preview'))
    for p in problems:
        print('AVISO', p)
    print(f'{len(lay)} títulos · {total}/{MAX_PIECES} pedazos · {nsheets} hojas'
          f'{" (+%d al final)" % (nsheets - len(sheet_t)) if nsheets > len(sheet_t) else ""} · '
          f'SUBTITLE.BIN {len(out)} B · {sum(len(ln) > 1 for *_, ln, _, _ in lay.values())} en 2 renglones')
    return 0


# ---------- vista previa: la pantalla como la arma el juego, a partir de los archivos generados ----------
def compose(sub, snmp, t, stage):
    """Imagen 320×120 (y 30..150 de pantalla) del título t con el encabezado del escenario `stage`."""
    ts = tim.scan(sub)
    sheet, parts = read_table(snmp)[t - 1]
    st = ts[2 + sheet]
    rgb = tim.bgr555(tim.cluts(sub, st)[0])        # la paleta que queda en VRAM es la de la hoja
    img = np.zeros((240, SCREEN_W, 3), np.uint8)
    img[:] = (24, 24, 40)

    def blit(idx, u, v, w, x, y):
        src = idx[v:v + ROW_H, u:u + w]
        m = src > 0
        img[y:y + ROW_H, x:x + w][m] = rgb[src[m], :3]
    sidx = tim.indices(sub, st)
    for u, v, w, x, y in parts:
        blit(sidx, u, v, w, x, y)
    didx = tim.indices(sub, ts[1])
    code = {a: struct.unpack_from('<I', snmp, a - BASE)[0] & 0xFFFF for a, *_ in STAGE_PATCH}
    two = stage >= 10
    x_dai = 0x78 if two else 0x80
    x_wa = code[0x800D7A0C] if two else code[0x800D7A18]
    digits = [(stage // 10, code[0x800D7AC8]), (stage % 10, code[0x800D7B58])] if two else \
        [(stage, code[0x800D7B54])]
    y_st = struct.unpack_from('<h', snmp, STAGE_Y - BASE)[0]
    blit(didx, 160, 0, 24, x_dai, y_st)
    blit(didx, 184, 0, 24, x_wa, y_st)
    for dgt, x in digits:
        blit(didx, 16 * dgt, 0, 16, x, 40)
    return img[30:150]


def preview(sub, snmp, outdir):
    os.makedirs(outdir, exist_ok=True)
    ids = [t for t in range(1, 130) if read_table(snmp)[t - 1][1]]
    cols, ph = 4, 120
    rows = (len(ids) + cols - 1) // cols
    big = np.zeros((rows * (ph + 2), cols * (SCREEN_W + 2), 3), np.uint8)
    for k, t in enumerate(ids):
        r, c = divmod(k, cols)
        big[r * (ph + 2):r * (ph + 2) + ph, c * (SCREEN_W + 2):c * (SCREEN_W + 2) + SCREEN_W] = \
            compose(sub, snmp, t, t % 100)
    for part in range(0, rows, 11):                  # PNG de ~44 títulos cada uno
        Image.fromarray(big[part * (ph + 2):(part + 11) * (ph + 2)]).save(
            os.path.join(outdir, f'titulos_{part // 11 + 1}.png'))
    ts = tim.scan(sub)
    for s, t in enumerate(ts[2:]):
        Image.fromarray(tim.bgr555(tim.cluts(sub, t)[0])[tim.indices(sub, t)], 'RGBA').save(
            os.path.join(outdir, f'hoja_{s:02d}.png'))


def dump():
    snmp = open(SNMP, 'rb').read()
    txt = titles()
    w = csv.writer(sys.stdout)
    w.writerow(['id', 'jp', 'hoja', 'recortes (u,v,ancho@x,y)'])
    for t, (s, parts) in enumerate(read_table(snmp), 1):
        w.writerow([t, txt.get(t, ('', ''))[0], s, ' '.join(f'{u},{v},{a}@{x},{y}' for u, v, a, x, y in parts)])


def selftest():
    snmp = open(SNMP, 'rb').read()
    table = read_table(snmp)
    ok = write_table(snmp, table) == snmp and sum(len(p) for _, p in table) == MAX_PIECES
    ok &= patch_code(patch_code(snmp, STAGE_PATCH), [(a, n, o) for a, o, n in STAGE_PATCH]) == snmp
    ts = tim.scan(open(SUB, 'rb').read())
    ok &= [t['off'] for t in ts[:3]] == [0x800, 0x13620, SHEET0] and len(ts) == 14
    print('subtitle selftest:', 'OK' if ok else 'FALLA')
    return ok


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'dump':
        dump()
    elif cmd == 'build' and len(sys.argv) == 4:
        sys.exit(build(sys.argv[2], sys.argv[3]))
    elif cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    else:
        sys.exit(__doc__)
