"""Estrés de la ventana de frases de batalla (#31): BXCLIST.BIN con TODAS las frases iguales a un texto de medición.
Renglones: regla de dígitos (8 px c/u, se lee dónde corta), y opcionalmente texto con espacios 0x20 reales ('~') para
ver cómo se dibujan frente a 0xA0.
Uso: mk_ancho_bxclist.py salida.BIN [n1,n2,...]   (n = dígitos por renglón; 'r' = renglón "Row~x~0x20 / Row x 0xA0")
"""
import json, os, sys
import bxclist
from mk_formato_test import ruler

WORK = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))


def row(spec, k):
    if spec == 'r':
        return f'Row~{k + 1}~0x20~~~spaces'
    if spec == 's':
        return f'Row {k + 1} 0xA0   spaces'
    return ruler(int(spec))


def main():
    out = sys.argv[1]
    specs = (sys.argv[2] if len(sys.argv) > 2 else '30,34,r,s').split(',')
    text = '\n'.join(row(s, k) for k, s in enumerate(specs))
    raw = text.encode('cp932').replace(b' ', b'\xa0').replace(b'~', b' ')
    data = open(bxclist.SRC, 'rb').read()
    raws, blocks = bxclist.parse(data)
    new = {}
    for line in open(os.path.join(WORK, 'dump', 'bxclist.jsonl'), encoding='utf-8'):
        r = json.loads(line)
        new[(r['pilot'], r['idx'])] = raw
    res = bxclist.build(raws, blocks, new)
    bxclist.parse(res)
    open(out, 'wb').write(res)
    print(f'{len(new)} frases = {text!r} → {out} ({len(res)} bytes)')


if __name__ == '__main__':
    main()
