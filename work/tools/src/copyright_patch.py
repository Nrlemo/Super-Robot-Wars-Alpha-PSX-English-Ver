"""Pantalla de copyright (G20, `TITLE/TITLEDAT.BIN` #2): ancho de cada línea según el inglés (#74).

El juego dibuja cada línea como un sprite **centrado** recortado de la hoja: registros de 32 bytes en TITL_GRP
(carga en 0x800FF190; 3 copias de la tabla, +0xF514, +0xF9F0, +0xFB78): u16 0x605 · u16 n · u16 0x1000|ancho (+4) ·
… · s16 dx, s16 dy (desde
el centro de pantalla) · … · u16 uv (u = byte bajo, v = byte alto) · … · u16 medio_ancho (+28) · u16 medio_alto = 8
(+30). El japonés trae el medio ancho de su línea (redondeado a 8 px), así que el inglés más largo salía cortado.
Este script mide la tinta de cada línea en el PNG ya renderizado (gfx/render/out/G20.png) y pone medio ancho =
(borde derecho de la tinta + 4 − u) / 2 y el ancho del recorte (+4, `0x1000 | ancho`) = el doble: la línea queda centrada con el mismo margen a cada lado. La línea
「©光プロ/アミューズビデオ/PLEX/アトランティス」 son dos sprites a la misma altura (el 2.º, u = 176, v = 160, comparte
renglón de la hoja con ©ビックウエスト): se pegan y se centran como un bloque.
La línea 2 de la hoja (© 1999 Project Cybuster, v = 16) no tiene registro: el juego no la muestra.

Uso:
  copyright_patch.py build <TITL_entrada|-> <G20.png> <dir_salida>   (- = iso_jp/OVL/TITL_GRP.BIN)
  copyright_patch.py report [<TITL_entrada>]                         registros del japonés
"""
import os
import struct
import sys

import numpy as np
from PIL import Image

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
JP = os.path.join(WORK, 'iso_jp', 'OVL', 'TITL_GRP.BIN')
MARGIN = 4


def records(buf):
    """Offsets de los registros de línea del copyright: tablas de 12 registros seguidos (n = 0..11) con la firma
    0x605 · n · … · CLUT 0x7C20 (+14) · … · 519 (+24) · n (+26) · medio ancho · 8."""
    def ok(o, n):
        h = struct.unpack_from('<16H', buf, o)
        return h[0] == 0x605 and h[1] == n and h[7] == 0x7C20 and h[12] == 519 and h[13] == n and h[15] == 8
    out = []
    for o in range(0, len(buf) - 32 * 12, 2):
        if all(ok(o + 32 * n, n) for n in range(12)):
            out += [o + 32 * n for n in range(12)]
    return out


def ink_right(png, u, v, end=256):
    """Borde derecho (exclusivo) de la tinta en las filas v..v+15, columnas u..end; None si no hay tinta."""
    im = Image.open(png)
    a = np.array(im)
    tr = im.info.get('transparency', 0)
    tr = {tr} if isinstance(tr, int) else {i for i, x in enumerate(tr) if x == 0} or {0}
    ink = ~np.isin(a[v:v + 16, u:end], list(tr))
    xs = np.where(ink.any(0))[0]
    return None if not len(xs) else u + int(xs.max()) + 1


def main(argv):
    if not argv or argv[0] not in ('build', 'report'):
        sys.exit(__doc__)
    src = argv[1] if len(argv) > 1 and argv[1] != '-' else JP
    buf = bytearray(open(src, 'rb').read())
    global JPBUF
    JPBUF = open(JP, 'rb').read()
    recs = records(bytes(buf))
    if len(recs) != 36:
        sys.exit(f'ERROR: se esperaban 36 registros de copyright (3 × 12) y hay {len(recs)}')
    if argv[0] == 'report':
        for o in recs:
            h = struct.unpack_from('<16h', buf, o)
            uv = h[8] & 0xFFFF
            print(f'+{o:#07x} n={h[1]:2d} dx={h[4]:4d} dy={h[5]:4d} u={uv & 255:3d} v={uv >> 8:3d} ancho={2 * h[14]}')
        return
    png, out = argv[2], argv[3]
    changed = 0
    for t in range(0, len(recs), 12):
        table = recs[t:t + 12]
        half = {}
        uvs = {o: struct.unpack_from('<H', buf, o + 16)[0] for o in table}
        for o in table:
            u, v = uvs[o] & 255, uvs[o] >> 8
            end = min([x & 255 for x in uvs.values() if x >> 8 == v and x & 255 > u] + [256])   # otro recorte del renglón
            right = ink_right(png, u, v, end)
            half[o] = (struct.unpack_from('<H', buf, o + 28)[0] if right is None
                       else min(-(-(right + MARGIN - u) // 2), (end - u) // 2, 127))   # el ancho del recorte es de 8 bits
            if t == 0 and right is not None:
                print(f'línea u={u:3d} v={v:3d}: ancho {2 * struct.unpack_from("<H", buf, o + 28)[0]} → {2 * half[o]}')
        # dos sprites a la misma altura (光プロ…/PLEX + /アトランティス): uno pegado al otro, centrados como un bloque
        rows = {}
        for o in table:
            rows.setdefault(struct.unpack_from('<h', buf, o + 10)[0], []).append(o)
        for dy, os_ in rows.items():
            if len(os_) == 2:
                a, b = sorted(os_, key=lambda o: struct.unpack_from('<h', buf, o + 8)[0])
                total = 2 * half[a] + 2 * half[b]
                struct.pack_into('<h', buf, a + 8, -total // 2 + half[a])
                struct.pack_into('<h', buf, b + 8, total // 2 - half[b])
        for o in table:
            if struct.unpack_from('<H', buf, o + 28)[0] != half[o]:
                struct.pack_into('<H', buf, o + 28, half[o])
                w4 = struct.unpack_from('<H', buf, o + 4)[0]          # 0x1000 | ancho del recorte
                assert w4 & 0x0FFF == 2 * struct.unpack_from('<H', bytes(JPBUF), o + 28)[0], hex(o)
                struct.pack_into('<H', buf, o + 4, (w4 & 0xF000) | 2 * half[o])
                changed += 1
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'TITL_GRP.BIN'), 'wb').write(buf)
    print(f'{changed} registros de copyright ensanchados (3 tablas)')


if __name__ == '__main__':
    main(sys.argv[1:])
