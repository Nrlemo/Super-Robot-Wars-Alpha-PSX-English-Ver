"""Construye la fuente inglesa de 1 byte: inserta los glifos de font/en_8px.txt en 8FONT_R.TIM
y genera la tabla de avances VWF y una vista previa.

Uso (desde work/): font_build.py [--tim-in iso_jp/FONTWIN/8FONT_R.TIM] [--glyphs font/en_8px.txt]
                   [--tim-out build/font/8FONT_R.TIM] [--table patches/vwf_table.bin]
                   [--wintex-in iso_jp/FONTWIN/WINTEX.BIN] [--wintex-out build/font/WINTEX.BIN]
                   [--preview notes/img/font_preview.png] [--text "frase de prueba"]
Solo toca las celdas de los bytes 0x20-0x7F (mitad derecha, filas 0-5). El resto (kana, símbolos) queda igual.
"""
import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image

from tim import bgr555
from vwf_table import cell_of

INK, SHADOW = 1, 3          # índices de la CLUT 0 (claro, oscuro), como en la fuente original
ROW_OFFSET = 4              # fila 0 del dibujo = fila 4 de la celda de 8x16
GLYPH_ROWS = 11


def parse_glyphs(path: Path) -> dict[int, tuple[list[str], int | None]]:
    glyphs, cur, rows, adv = {}, None, [], None
    for line in path.read_text(encoding='utf-8').splitlines() + ['== END']:
        if line.startswith('#') and cur is None:
            continue
        if line.startswith('== '):
            if cur is not None and adv == 'keep':
                glyphs[cur] = ([], 'keep')
            elif cur is not None:
                assert len(rows) == GLYPH_ROWS, f'glifo {cur!r}: {len(rows)} filas'
                assert len({len(r) for r in rows}) == 1, f'glifo {cur!r}: filas de distinto ancho'
                glyphs[cur] = (rows, adv)
            parts = line[3:].split()
            name = parts[0]
            adv = 'keep' if 'keep' in parts[1:] else next((int(p[4:]) for p in parts[1:] if p.startswith('adv=')), None)
            cur = None if name == 'END' else (0x20 if name == 'space' else int(name, 16) if name.startswith('0x') else ord(name))
            rows = []
        elif cur is not None and line.strip():
            rows.append(line.strip())
    return glyphs


class Tim4:
    """TIM de 4 bpp editable in-place (conserva cabecera y CLUT)."""

    def __init__(self, data: bytes):
        self.data = bytearray(data)
        flags = struct.unpack_from('<I', data, 4)[0]
        assert (flags & 3) == 0 and flags & 8, 'se espera TIM 4bpp con CLUT'
        clut_len = struct.unpack_from('<I', data, 8)[0]
        self.clut = np.frombuffer(bytes(data[20:52]), '<u2')
        o = 8 + clut_len
        _, _, _, vw, self.h = struct.unpack_from('<IHHHH', data, o)
        self.w = vw * 4
        self.pix = o + 12

    def set(self, x: int, y: int, v: int):
        i = self.pix + y * (self.w // 2) + x // 2
        b = self.data[i]
        self.data[i] = (b & 0xF0) | v if x % 2 == 0 else (b & 0x0F) | (v << 4)

    def get(self, x: int, y: int) -> int:
        b = self.data[self.pix + y * (self.w // 2) + x // 2]
        return b & 0xF if x % 2 == 0 else b >> 4


def build(tim_in: Path | bytes, glyphs: dict, tim_out: Path | None, table_out: Path | None) -> tuple[Tim4, bytes]:
    tim = Tim4(tim_in if isinstance(tim_in, bytes) else tim_in.read_bytes())
    table = bytearray([8] * 256)
    for ch in list(range(0x20, 0x80)) + [b for b in glyphs if b >= 0x80]:
        r, c = cell_of(ch)
        x0, y0 = c * 8, r * 16
        if glyphs.get(ch, (None, None))[1] == 'keep':  # glifo y avance originales
            table[ch] = 8
            continue
        for y in range(16):                       # limpiar celda
            for x in range(8):
                tim.set(x0 + x, y0 + y, 0)
        if ch not in glyphs:
            continue
        rows, adv = glyphs[ch]
        w = len(rows[0])
        assert w <= 7, f'{chr(ch)!r}: ancho {w} > 7 (no entra la sombra)'
        ink = {(x, y) for y, row in enumerate(rows) for x, p in enumerate(row) if p == '#'}
        for x, y in ink:                           # sombra primero, tinta encima
            if (x + 1, y + 1) not in ink and y + 1 + ROW_OFFSET < 16:
                tim.set(x0 + x + 1, y0 + y + 1 + ROW_OFFSET, SHADOW)
        for x, y in ink:
            tim.set(x0 + x, y0 + y + ROW_OFFSET, INK)
        table[ch] = adv if adv is not None else w + 1
    if tim_out:
        tim_out.parent.mkdir(parents=True, exist_ok=True)
        tim_out.write_bytes(tim.data)
    if table_out:
        table_out.write_bytes(table)
    return tim, bytes(table)


WINTEX_FONT_OFF = 0x800  # entrada 0 de FONTWIN/WINTEX.BIN = otra copia de la fuente (TIM de 33.152 bytes)


def build_wintex(wintex_in: Path, glyphs: dict, wintex_out: Path, tim_size: int):
    """La copia que usa el cuadro de diálogo en pantalla está dentro de WINTEX.BIN (notes/fuente_en.md)."""
    d = bytearray(wintex_in.read_bytes())
    tim, _ = build(bytes(d[WINTEX_FONT_OFF:WINTEX_FONT_OFF + tim_size]), glyphs, None, None)
    d[WINTEX_FONT_OFF:WINTEX_FONT_OFF + tim_size] = tim.data
    wintex_out.parent.mkdir(parents=True, exist_ok=True)
    wintex_out.write_bytes(d)


def preview(tim: Tim4, table: bytes, lines: list[str], out: Path, scale: int = 3):
    """Simula el maquetado del juego (sprites de 8x16, avance = tabla) en una caja de 240 px."""
    clut = bgr555(tim.clut)
    img = np.zeros((16 * len(lines) + 8, 248, 4), np.uint8)
    img[..., :3] = (8, 8, 24)
    img[..., 3] = 255
    for li, text in enumerate(lines):
        x = 4
        for ch in text.replace(' ', '\xa0').encode('latin1'):
            r, c = cell_of(ch)
            for yy in range(16):
                for xx in range(8):
                    v = tim.get(c * 8 + xx, r * 16 + yy)
                    px, py = x + xx, 4 + li * 16 + yy
                    if v and px < img.shape[1]:
                        img[py, px] = clut[v]
            x += table[ch]
        img[:, 4 + 240] = (200, 40, 40, 255)      # límite de 240 px
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(out)


SAMPLE = [
    'Tashiro: Ugh... What the hell?!',
    "The EOT fleet we built is being torn",
    "apart like paper! Get me a status report!",
    'Amuro: "Gundam, launching!" 0123456789',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz',
    "!?.,'\":;-()&/+*=%<>[]_~@#$ {|} Mk-II",
]

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--tim-in', default='iso_jp/FONTWIN/8FONT_R.TIM', type=Path)
    ap.add_argument('--glyphs', default='font/en_8px.txt', type=Path)
    ap.add_argument('--tim-out', default='build/font/8FONT_R.TIM', type=Path)
    ap.add_argument('--table', default='patches/vwf_table.bin', type=Path)
    ap.add_argument('--preview', default='notes/img/font_preview.png', type=Path)
    ap.add_argument('--wintex-in', default='iso_jp/FONTWIN/WINTEX.BIN', type=Path)
    ap.add_argument('--wintex-out', default='build/font/WINTEX.BIN', type=Path)
    a = ap.parse_args()
    g = parse_glyphs(a.glyphs)
    tim, table = build(a.tim_in, g, a.tim_out, a.table)
    build_wintex(a.wintex_in, g, a.wintex_out, len(tim.data))
    preview(tim, table, SAMPLE, a.preview)
    widths = [sum(table[b] for b in s.replace(' ', '\xa0').encode('latin1')) for s in SAMPLE]
    print(f'{len(g)} glifos → {a.tim_out} + {a.wintex_out}, tabla → {a.table}, preview → {a.preview}')
    print('ancho de las frases de prueba (px):', widths)
