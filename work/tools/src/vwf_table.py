"""Genera la tabla de avances VWF (256 bytes, índice = byte del carácter) desde el ancho de tinta de 8FONT_R.TIM.

Uso: vwf_table.py <8FONT_R.TIM> <salida.bin>
Avance = columna derecha de tinta + 1 (la sombra de 1 px hace de separación). Espacio = 4 px.
Bytes sin glifo ASCII medido (kana medio ancho, etc.) conservan el avance original de 8 px.
"""
import sys

import numpy as np

from tim import read_tim

SPACE = 4


def cell_of(byte: int):
    """Celda (fila, columna) de 8x16 que usa FUN_8001885C para un byte: índice = b-0x20 (b>=0xA0: b-0x40)."""
    i = (byte - 0x40 if byte >= 0xA0 else byte - 0x20) & 0xFF
    return i >> 4, 16 + (i & 15)


def ascii_cells():
    return {ch: cell_of(ch) for ch in range(0x20, 0x80)}


def build(tim_path) -> bytes:
    _, _, idx = read_tim(open(tim_path, 'rb').read())
    table = bytearray([8] * 256)
    for ch, (r, c) in ascii_cells().items():
        cols = np.where((idx[r * 16:(r + 1) * 16, c * 8:(c + 1) * 8] != 0).any(0))[0]
        if len(cols):
            table[ch] = int(cols.max()) + 1
    table[0x20] = SPACE
    return bytes(table)


if __name__ == '__main__':
    t = build(sys.argv[1])
    open(sys.argv[2], 'wb').write(t)
    print(' '.join(f'{chr(i)}{t[i]}' for i in range(0x20, 0x7f)))
