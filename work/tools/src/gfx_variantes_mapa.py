#!/usr/bin/env python3
"""Renderiza G33–G36 (mapa 「現在位置」) con varias fuentes para compararlas, sin tocar los CSV.

Uso: python3 work/tools/src/gfx_variantes_mapa.py        (salida: work/gfx/render/variantes_mapa/<variante>/)
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import gfx_render as R  # noqa: E402

# nombre: (font, size, style) para todas las cajas
VARIANTES = {
    'I_cond12_solid': ('DejaVuSansCondensed-Bold', 12, 'solid'),
    'J_dejavu11_solid': ('DejaVuSans-Bold', 11, 'solid'),
    'K_cond13_solid': ('DejaVuSansCondensed-Bold', 13, 'solid'),
    'L_game8_solid': ('game8', 8, 'solid'),
}
PIEZAS = ['G33', 'G34', 'G35', 'G36']


def main():
    orig = R.RENDER
    base = os.path.join(orig, 'variantes_mapa')
    for nombre, (font, size, style) in VARIANTES.items():
        tmp = tempfile.mkdtemp()
        for pid in PIEZAS:
            with open(os.path.join(orig, pid + '.csv'), encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            for r in rows:
                r['font'], r['size'], r['style'] = font, str(size), style
            with open(os.path.join(tmp, pid + '.csv'), 'w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=R.COLS)
                w.writeheader()
                w.writerows(rows)
        R.RENDER = tmp
        R.OUT = os.path.join(base, nombre)
        print('==', nombre)
        R.render(PIEZAS)


if __name__ == '__main__':
    main()
