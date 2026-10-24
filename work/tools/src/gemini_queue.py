#!/usr/bin/env python3
"""Plan de trabajos de traducción con Gemini: uno por lote pendiente (una rama cada uno). Salida JSON:
[{"fmt","spec","branch","filas","pendientes"}]. Sin la ISO (lee work/dump/).
Cada trabajo lleva `n` y `total`: su posición ("lote n de total") entre TODOS los lotes de su formato, hechos o no
(la partición no depende de lo traducido: agrupa por filas totales).
Uso: gemini_queue.py [--formatos snmsg,script,bxclist,deadmess,em] [--max-filas 450] [--saltear-ramas ramas.txt] [--max-trabajos N]
     gemini_queue.py --todos      # también los lotes ya terminados (para contar el total por tipo)
     gemini_queue.py --resumen    # tabla: lotes, terminados y filas por formato"""
import argparse, collections, csv, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lote as L  # noqa: E402


def grupos(cuentas: dict[int, tuple[int, int]], tope: int) -> list[tuple[int, int, int, int]]:
    """Agrupa claves consecutivas hasta `tope` filas: (desde, hasta, filas, pendientes)."""
    out, cur = [], None
    for k in sorted(cuentas):
        n, p = cuentas[k]
        if cur and cur[2] + n > tope:
            out.append(tuple(cur)); cur = None
        if cur is None:
            cur = [k, k, 0, 0]
        cur[1] = k; cur[2] += n; cur[3] += p
    if cur:
        out.append(tuple(cur))
    return out


def plan(formatos, tope, todos=False):
    jobs = []
    for fmt in formatos:
        rows = L.read_jsonl(L.DUMP / f'{fmt}.jsonl')
        if fmt == 'snmsg':
            smap = {int(r['slot']): r for r in csv.DictReader(open(L.DUMP / 'sndata_map.csv', encoding='utf-8'))}
            c = collections.defaultdict(lambda: [0, 0])
            for r in rows:
                b = smap.get(r['id'], {}).get('bloque')
                if b is not None and b != '':
                    c[int(b)][0] += 1; c[int(b)][1] += not r.get('en')
            for b, (n, p) in sorted(c.items()):
                jobs.append({'fmt': fmt, 'spec': f'--bloque {b}', 'branch': f'traduccion/mapa-b{b:03d}', 'filas': n, 'pendientes': p})
        else:
            campo = L.RANGE_FIELD[fmt]
            c = collections.defaultdict(lambda: [0, 0])
            for r in rows:
                c[r[campo]][0] += 1; c[r[campo]][1] += not r.get('en')
            for a, z, n, p in grupos({k: tuple(v) for k, v in c.items()}, tope):
                pref = {'script': 's', 'bxclist': '', 'deadmess': '', 'em': ''}[fmt]
                rng = f'{a}-{z}' if a != z else f'{a}'
                jobs.append({'fmt': fmt, 'spec': rng, 'branch': f'traduccion/{fmt}-{pref}{rng}', 'filas': n, 'pendientes': p})
    for fmt in formatos:
        mios = [j for j in jobs if j['fmt'] == fmt]
        for i, j in enumerate(mios, 1):
            j['n'], j['total'] = i, len(mios)
    return jobs if todos else [j for j in jobs if j['pendientes']]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--formatos', default='snmsg,script,bxclist,deadmess,em')
    ap.add_argument('--max-filas', type=int, default=450)
    ap.add_argument('--saltear-ramas', help='archivo con ramas remotas que ya existen (una por línea)')
    ap.add_argument('--max-trabajos', type=int, default=0)
    ap.add_argument('--todos', action='store_true', help='incluir los lotes sin filas pendientes')
    ap.add_argument('--resumen', action='store_true', help='tabla por formato en vez de JSON')
    a = ap.parse_args()
    jobs = plan(a.formatos.split(','), a.max_filas, a.todos or a.resumen)
    if a.resumen:
        print(f'{"formato":10} {"lotes":>6} {"terminados":>11} {"parciales":>10} {"filas":>7} {"traducidas":>11} {"%":>6}')
        for fmt in a.formatos.split(','):
            m = [j for j in jobs if j['fmt'] == fmt]
            f, p = sum(j['filas'] for j in m), sum(j['pendientes'] for j in m)
            print(f'{fmt:10} {len(m):>6} {sum(1 for j in m if not j["pendientes"]):>11} {sum(1 for j in m if 0 < j["pendientes"] < j["filas"]):>10} {f:>7} {f - p:>11} {100 * (f - p) / max(f, 1):>6.1f}')
        return
    if a.saltear_ramas:
        hechas = {l.strip().removeprefix('refs/heads/') for l in open(a.saltear_ramas) if l.strip()}
        jobs = [j for j in jobs if j['branch'] not in hechas]
    if a.max_trabajos:
        jobs = jobs[:a.max_trabajos]
    print(json.dumps(jobs, ensure_ascii=False))


if __name__ == '__main__':
    main()
