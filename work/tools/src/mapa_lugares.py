"""Mapa 「現在位置」 (G33–G36, `BUSTUP/MAP.BIN`): lugares en inglés con cajas dinámicas (#188).

Los recortes no están en el código: cada escena los da en `SCRIPT.BIN`, op 0x0040 sub 4 (512 instancias). `arg` = mapa
(1→G33, 2→G34, 3 y 4→G35 —entradas 5 y 7, idénticas—, 5→G36); datos ASCII `x 199 ancho 16 u v mx my`, con x = 295 − ancho
(el rótulo se alinea a la derecha; el marco del juego crece con el ancho). Ver work/notes/graficos.md.

Este script:
  1. `lugares_mapa.csv`: una fila por recorte distinto (hoja, u, v, ancho del japonés) con su inglés. Algunas escenas
     muestran solo el principio del rótulo japonés (連邦軍極東支部 de 連邦軍極東支部 基地付近): son filas aparte.
  2. Dibuja cada inglés grande (DejaVu Sans Bold 14, la altura de los kanji) y reempaqueta la hoja desde v = 32
     (renglones de 16 px; la cabecera v < 32 la sigue dibujando gfx_render con Gxx.csv, fila H1).
  3. `patch_script(scripts)`: reescribe u, v, ancho y x de cada instancia (lo llama script_bin.py build).
Ancho máximo de una caja: MAXW (≤ 3/4 de pantalla con el marco). `en` vacío = se copia el japonés tal cual.

Uso:
  mapa_lugares.py init      crea lugares_mapa.csv (inglés tomado de G33–G36.csv; no pisa uno existente)
  mapa_lugares.py render    escribe out/G33–G36.png (+ _preview) y avisa lo que no entra
"""
import csv
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx_render as R  # noqa: E402
import script_bin as S  # noqa: E402
import tim  # noqa: E402

CSV = os.path.join(R.RENDER, 'lugares_mapa.csv')
SHEET = {1: 'G33', 2: 'G34', 3: 'G35', 4: 'G35', 5: 'G36'}
OP = (0x0040, 4)
RIGHT = 295            # borde derecho del rótulo en pantalla
TOP, ROW, ROWS = 32, 16, 14
FONT, SIZE, MIN_SIZE = 'DejaVuSans-Bold', 14, 11
MAXW = 231             # 3/4 de 320 = 240, menos el marco
FIELDS = ['hoja', 'u', 'v', 'w', 'usos', 'jp', 'en']

# recortes que muestran solo el principio del rótulo japonés: (hoja, u, v, ancho) → (jp visible, inglés)
PARTIAL = {
    ('G33', 0, 96, 111): ('連邦軍極東支部', 'Fed. Far East Branch'),
    ('G34', 64, 32, 95): ('アメリカ西海岸', 'US West Coast'),
    ('G34', 0, 128, 87): ('南アタリア島', 'South Ataria Island'),
    ('G35', 0, 80, 79): ('衛星軌道上', 'In Orbit'),
    ('G35', 0, 96, 95): ('ア・バオア・クー', 'A Baoa Qu'),
}


def instances(scripts):
    """(instrucción, hoja, [x, y, w, h, u, v, mx, my]) de cada rótulo de lugar."""
    for s in scripts:
        for ins in s:
            if (ins['op'], ins['sub']) == OP:
                yield ins, SHEET[ins['arg']], [int(t) for t in ins['data'].rstrip(b'\0').decode().split()]


def init():
    if os.path.exists(CSV):
        sys.exit(f'ya existe {CSV}')
    scripts = S.parse(open(S.SRC, 'rb').read())[0]
    uses = Counter((g, n[4], n[5], n[2]) for _, g, n in instances(scripts))
    boxes = {g: [r for r in csv.DictReader(open(R.csv_path(g), encoding='utf-8')) if r['caja'][0] == 'R']
             for g in set(SHEET.values())}
    rows = []
    for (g, u, v, w), n in sorted(uses.items(), key=lambda t: (t[0][0], t[0][2], t[0][1], t[0][3])):
        box = next(r for r in boxes[g] if abs(int(r['y']) - 1 - v) <= 1 and abs(int(r['x']) - u) <= 3)
        jp, en = PARTIAL.get((g, u, v, w), (box['jp'], box['en']))
        rows.append(dict(hoja=g, u=u, v=v, w=w, usos=n, jp=jp, en=en))
    with open(CSV, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    print(len(rows), 'recortes →', CSV)


def rows():
    return list(csv.DictReader(open(CSV, encoding='utf-8')))


def text_mask(en):
    """Inglés → máscara bool (alto ≤ 15: la sombra ocupa el renglón 16). Grande primero; Condensed antes de achicar."""
    paths = [R.find_font(FONT), R.find_font(FONT.replace('-', 'Condensed-', 1))]
    for px in range(SIZE, MIN_SIZE - 1, -1):
        for path in paths:
            a = R.ttf_render(en, path, px, False, tight=True)
            if a.shape[1] + 3 <= MAXW and a.shape[0] <= ROW - 1:
                return a, True
    return a, False


def box_width(text_w):
    return min(-(-(text_w + 3 + 1) // 8) * 8 - 1, MAXW)    # 1 px a cada lado + sombra; 8k − 1 como el japonés


def layout():
    """{hoja: [(fila, máscara | None, (u, v, w) nuevos)]} y avisos. Empaquetado: más anchos primero, primer hueco."""
    out, problems = {}, []
    for g in sorted(set(SHEET.values())):
        items = []
        for r in rows():
            if r['hoja'] != g:
                continue
            if r['en'].strip():
                m, ok = text_mask(r['en'].strip())
                if not ok:
                    problems.append(f"{g} {r['jp']}: \"{r['en']}\" no entra en {MAXW} px (mide {m.shape[1]})")
                items.append((r, m, box_width(m.shape[1])))
            else:
                items.append((r, None, int(r['w'])))
        free = [0] * ROWS
        placed = []
        for r, m, w in sorted(items, key=lambda t: -t[2]):
            k = next((k for k in range(ROWS) if free[k] + w <= 256), None)
            if k is None:
                problems.append(f"{g}: no hay lugar en la hoja para \"{r['en'] or r['jp']}\"")
                continue
            placed.append((r, m, (free[k], TOP + ROW * k, w)))
            free[k] += w + 1
        out[g] = placed
    return out, problems


def render():
    lay, problems = layout()
    for g, placed in lay.items():
        p, buf, t, idx, pr = R.render_boxes(g)       # cabecera (H1) y el resto como hoy
        problems += [x for x in pr if ' H1' in x]
        orig = tim.indices(buf, t)
        bg = min(R.G.transparent(buf, t))
        idx[TOP:, :] = bg
        lum = R.palette_lum(buf, t)
        cand = [i for i in range(len(lum)) if i not in R.G.transparent(buf, t)]
        ink, shadow = max(cand, key=lambda i: lum[i]), min(cand, key=lambda i: lum[i])
        for r, m, (u, v, w) in placed:
            if m is None:
                ou, ov, ow = int(r['u']), int(r['v']), int(r['w'])
                idx[v:v + ROW, u:u + ow] = orig[ov:ov + ROW, ou:ou + ow]
            else:
                R.draw_shadow(idx, m, u + 1, v, ink, shadow)
        R.save(p, buf, t, idx)
        print('generado', g, f'({len(placed)} lugares)')
    for x in problems:
        print('AVISO', x)
    return problems


def patch_script(scripts):
    """Reescribe los rótulos de lugar de SCRIPT con el nuevo empaquetado. Devuelve cuántas instancias cambió."""
    if not os.path.exists(CSV):
        return 0
    lay, _ = layout()
    new = {(g, int(r['u']), int(r['v']), int(r['w'])): uvw for g, placed in lay.items() for r, _, uvw in placed}
    n = 0
    for ins, g, nums in instances(scripts):
        x, y, w, h, u, v = nums[:6]
        nu, nv, nw = new[(g, u, v, w)]
        nums[:6] = [x + w - nw, y, nw, h, nu, nv]       # mismo borde derecho (incluida la excepción 234/63)
        ins['data'] = ' '.join(map(str, nums)).encode() + b'\0'
        n += 1
    return n


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'init':
        init()
    elif cmd == 'render':
        render()
    else:
        print(__doc__)
