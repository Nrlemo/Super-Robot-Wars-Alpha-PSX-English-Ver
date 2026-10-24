"""Margen de ancho de las traducciones frente a cambios en la fuente VWF (#50).

Uso (desde work/):
  font_margen.py                         # margen actual por formato + pares de letras frecuentes
  font_margen.py --delta r=+1,f=+1       # cuántas líneas dejarían de entrar con esos avances cambiados
  font_margen.py --each r,f,t,{A0}       # prueba +1 en cada carácter por separado
  font_margen.py --delta t=+1 --list 20  # además lista las líneas que se romperían

Mide igual que check_text.py (misma tabla, mismas reservas). Además de los formatos con límite de px, informa el
nombre más ancho de pilotos, unidades y armas (no tienen tope de px verificado: los menús se miran en el juego).
Los caracteres se nombran como en el texto, salvo el espacio inglés, que es {A0}.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import check_text as ct

WORK = ct.WORK
PAIRS = ['rn', 'rt', 'ri', 'rf', 'ft', 'ff', 'fi', 'fl', 'tt', 'tr', 'r.', 'r,', 'r!', 'r?', "r'", 'f.', 't.',
         'l!', 'i!', '.{A0}', ',{A0}', '!{A0}', '?{A0}', '{A0}(', '){A0}', 'li', 'il', 'll']


def parse_delta(s: str) -> dict:
    out = {}
    for item in filter(None, (s or '').split(',')):
        ch, _, v = item.partition('=')
        out[0xA0 if ch == '{A0}' else ord(ch)] = int(v)
    return out


def table_with(delta: dict) -> bytes:
    t = bytearray(ct.ADV)
    for b, d in delta.items():
        t[b] = max(0, t[b] + d)
    return bytes(t)


def lines_of(fmt_names):
    """(formato, id, n_línea, texto, límite_px) de cada línea medible."""
    for name in fmt_names:
        f = ct.FORMATS[name]
        path = WORK / 'dump' / f.file
        if f.line_px is None or not path.exists():
            continue
        for key, jp, en, _cap, reserve in ct.iter_rows(name, path):
            if not en:
                continue
            ls = en.split('\n')
            for n, ln in enumerate(ls, 1):
                lim = f.line_px - (reserve[0] if n == 1 else 0) - (reserve[1] if n == len(ls) else 0)
                yield name, key, n, ln, lim, f.kana_px


def names():
    """(tipo, texto) de nombres de piloto, unidad y arma traducidos."""
    p = WORK / 'dump' / 'pilot.jsonl'
    if p.exists():
        for line in open(p, encoding='utf-8'):
            r = json.loads(line)
            for k in ('full_en', 'short_en'):
                if r.get(k):
                    yield f'piloto.{k[:-3]}', r[k]
    p = WORK / 'dump' / 'robot.jsonl'
    if p.exists():
        for line in open(p, encoding='utf-8'):
            r = json.loads(line)
            if r.get('name_en'):
                yield 'unidad', r['name_en']
            for w in r.get('weapons', []):
                if w.get('name_en'):
                    yield 'arma', w['name_en']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', help='formatos (por defecto todos los que tienen límite de px)')
    ap.add_argument('--delta', help='cambios de avance, p. ej. r=+1,{A0}=+1')
    ap.add_argument('--each', help='probar +1 en cada uno de estos caracteres por separado')
    ap.add_argument('--list', type=int, default=0, help='listar hasta N líneas que se romperían con --delta')
    a = ap.parse_args(argv)
    fmts = a.only.split(',') if a.only else [k for k, f in ct.FORMATS.items() if f.line_px]
    rows = [(n, k, i, ln, lim, kp, ct.line_px(ln, kp)) for n, k, i, ln, lim, kp in lines_of(fmts)]
    texts, reserve = {}, {}
    for name in fmts:
        path = WORK / 'dump' / ct.FORMATS[name].file
        if path.exists():
            for key, _jp, en, _cap, res in ct.iter_rows(name, path):
                texts[(name, key)], reserve[(name, key)] = en, res[0]

    print(f'Tabla base: {ct.ADV_SRC}')
    print(f'{"formato":9} {"líneas":>7} {"pasadas":>8} {"margen 0":>9} {"1-2":>6} {"3-5":>6} {"6-10":>6} {">10":>7}')
    for name in fmts:
        sl = [lim - px for n, _k, _i, _l, lim, _kp, px in rows if n == name]
        if not sl:
            continue
        c = lambda lo, hi: sum(lo <= s <= hi for s in sl)
        print(f'{name:9} {len(sl):7} {sum(s < 0 for s in sl):8} {c(0, 0):9} {c(1, 2):6} {c(3, 5):6} {c(6, 10):6} '
              f'{sum(s > 10 for s in sl):7}')

    if not a.delta and not a.each:
        game = Counter()
        for *_x, ln, _lim, _kp, _px in rows:
            g = ct.to_game(ln)
            for p in PAIRS:
                game[p] += g.count(p)
        print('\nPares en el texto (para elegir capturas):')
        print('  ' + '  '.join(f'{p.replace("{A0}", "␣")}:{game[p]}' for p in PAIRS))

    def report(delta, label):
        adv = table_with(delta)
        broken = [(n, k, i, ln, lim, kp, ct.line_px(ln, kp, adv), px) for n, k, i, ln, lim, kp, px in rows]
        broken = [b for b in broken if b[6] > b[4] >= b[7]]
        per = Counter(b[0] for b in broken)
        # filas rotas que no entran ni re-cortando las líneas (respetando los \n del hablante, o re-fluyendo todo)
        stuck, base = Counter(), ct.ADV
        ct.ADV = adv
        try:
            for n, k in sorted({(b[0], b[1]) for b in broken}):
                f = ct.FORMATS[n]
                en = texts[(n, k)]
                width = f.line_px - reserve[(n, k)]
                if all(len(ct.wrap(en, width, f.kana_px, kb)) > f.max_lines for kb in (True, False)):
                    stuck[n] += 1
        finally:
            ct.ADV = base
        nm = list(names())
        wide = {}
        for kind, t in nm:
            old, new = ct.line_px(t, 12), ct.line_px(t, 12, adv)
            m = wide.setdefault(kind, [0, 0, 0])
            m[0], m[1], m[2] = max(m[0], old), max(m[1], new), m[2] + (new > old)
        print(f'\n{label}: {len(broken)} líneas dejan de entrar  ' +
              ' '.join(f'{k}:{v}' for k, v in sorted(per.items())) +
              f'  → sin arreglo re-cortando: {sum(stuck.values())} ' +
              ' '.join(f'{k}:{v}' for k, v in sorted(stuck.items())))
        print('  nombres (máx. px antes→después, cuántos crecen): ' +
              '  '.join(f'{k} {v[0]}→{v[1]} ({v[2]})' for k, v in wide.items()))
        for b in broken[:a.list]:
            print(f'  {b[0]} {b[1]} L{b[2]} {b[7]}→{b[6]}/{b[4]} px | {b[3]}')

    if a.each:
        for ch in a.each.split(','):
            report(parse_delta(f'{ch}=+1'), f'+1 en {ch}')
    if a.delta:
        report(parse_delta(a.delta), f'delta {a.delta}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
