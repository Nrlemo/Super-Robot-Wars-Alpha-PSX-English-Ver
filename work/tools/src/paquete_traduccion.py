#!/usr/bin/env python3
"""Arma traduccion/paquetes/ para traducir con otra IA: comun/ (prompt + referencias) + mapa/ (un lote por
bloque de SNMSG) + intermision/ (escenas de SCRIPT agrupadas). Uso: paquete_traduccion.py RAW_DIR
RAW_DIR = salida de `lote.py sacar ... --salida RAW_DIR/{snmsg_NNN,script_NNN}.jsonl` (con .reparto/.terminos)."""
import csv, glob, json, os, re, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'traduccion', 'paquetes')
MAX_FILAS = 450


def leer(f):
    return [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]


def escribir(f, filas):
    with open(f, 'w', encoding='utf-8') as o:
        for r in filas:
            r.get('ctx', {}).pop('chs', None)
            o.write(json.dumps(r, ensure_ascii=False) + '\n')


def tsv_union(fs, dst):
    rows, head = {}, None
    for f in fs:
        if not os.path.exists(f):
            continue
        for i, l in enumerate(open(f, encoding='utf-8').read().splitlines()):
            if i == 0:
                head = head or l
            elif l:
                rows.setdefault(l.split('\t')[0], l)
    if head:
        open(dst, 'w', encoding='utf-8').write('\n'.join([head] + list(rows.values())) + '\n')


def slug(s):
    return re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_')[:40]


def main(raw):
    shutil.rmtree(OUT, ignore_errors=True)
    for d in ('comun/referencia', 'mapa', 'intermision'):
        os.makedirs(os.path.join(OUT, d))
    R = os.path.join(ROOT, 'traduccion', 'referencia')
    for f in ('protagonistas.md', 'series.csv', 'terminologia.csv', 'lugares.csv', 'facciones.csv', 'naves.csv',
              'frases_fijas.csv', 'misiones.csv', 'hablantes.csv', 'creditos_y_canciones.md'):
        shutil.copy(os.path.join(R, f), os.path.join(OUT, 'comun', 'referencia', f))
    shutil.copy(os.path.join(ROOT, 'work', 'notes', 'guia_estilo_personajes.md'),
                os.path.join(OUT, 'comun', 'referencia', 'guia_estilo_personajes.md'))
    misiones = {}
    for r in csv.DictReader(open(os.path.join(R, 'misiones.csv'), encoding='utf-8')):
        for b in (r['bloques_sndata'] or '').split():
            misiones[b] = r
    n_mapa = 0
    for f in sorted(glob.glob(os.path.join(raw, 'snmsg_*.jsonl'))):
        b = str(int(re.search(r'(\d+)', os.path.basename(f)).group(1)))
        filas = leer(f)
        if not filas:
            continue
        m = misiones.get(b, {})
        ctx = filas[0].get('ctx', {})
        esc = ctx.get('escenario', '?'); ruta = slug(ctx.get('ruta') or 'comun')
        base = f"mapa_b{int(b):03d}_esc{esc}_{ruta}_{slug(ctx.get('mision') or m.get('en', ''))}"
        dst = os.path.join(OUT, 'mapa', base)
        escribir(dst + '.jsonl', filas)
        for e in ('reparto', 'terminos'):
            if os.path.exists(f + f'.{e}.tsv'):
                shutil.copy(f + f'.{e}.tsv', dst + f'.{e}.tsv')
        n_mapa += 1
    grupos, cur, n = [], [], 0
    for f in sorted(glob.glob(os.path.join(raw, 'script_*.jsonl'))):
        filas = leer(f)
        if not filas:
            continue
        num = int(re.search(r'(\d+)', os.path.basename(f)).group(1))
        if cur and n + len(filas) > MAX_FILAS:
            grupos.append(cur); cur, n = [], 0
        cur.append((num, f, filas)); n += len(filas)
    if cur:
        grupos.append(cur)
    for g in grupos:
        a, z = g[0][0], g[-1][0]
        base = os.path.join(OUT, 'intermision', f'intermision_s{a:03d}-s{z:03d}' if a != z else f'intermision_s{a:03d}')
        escribir(base + '.jsonl', [r for _, _, fs in g for r in fs])
        for e in ('reparto', 'terminos'):
            tsv_union([f + f'.{e}.tsv' for _, f, _ in g], base + f'.{e}.tsv')
    print(f'mapa: {n_mapa} lotes · intermision: {len(grupos)} lotes')


if __name__ == '__main__':
    main(sys.argv[1])
