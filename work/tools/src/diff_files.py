"""Compara dos árboles de archivos extraídos (JP vs CHS) y clasifica cada región modificada.

Uso: diff_files.py <dir_jp> <dir_chs> <reporte.md> [<runs.json>]

Clasificación por run (bytes contiguos modificados, uniendo huecos de <= GAP bytes):
  texto    : >= 60% de los bytes JP y CHS forman caracteres SJIS de doble byte
  puntero  : run corto (<= 4 bytes) fuera de texto — candidatos a offsets/longitudes
  binario  : el resto (gráficos, datos, código)
"""
import json
import sys
from collections import Counter
from pathlib import Path

GAP = 4


def is_lead(b: int) -> bool:
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF


def sjis_ratio(buf: bytes) -> float:
    if not buf:
        return 0.0
    i = covered = 0
    while i < len(buf):
        if is_lead(buf[i]) and i + 1 < len(buf) and 0x40 <= buf[i + 1] <= 0xFC and buf[i + 1] != 0x7F:
            covered += 2
            i += 2
        else:
            i += 1
    return covered / len(buf)


def runs_of(a: bytes, b: bytes) -> list[tuple[int, int]]:
    n = min(len(a), len(b))
    diff = [i for i in range(n) if a[i] != b[i]]
    if len(a) != len(b):
        diff += list(range(n, max(len(a), len(b))))
    if not diff:
        return []
    out, s, p = [], diff[0], diff[0]
    for i in diff[1:]:
        if i > p + GAP + 1:
            out.append((s, p + 1))
            s = i
        p = i
    out.append((s, p + 1))
    return out


def classify(a: bytes, b: bytes, s: int, e: int) -> str:
    # ampliar 2 bytes a cada lado para no partir caracteres de doble byte
    ctx_a, ctx_b = a[max(0, s - 2):e + 2], b[max(0, s - 2):e + 2]
    if e - s >= 2 and sjis_ratio(ctx_a) >= 0.6 and sjis_ratio(ctx_b) >= 0.6:
        return 'texto'
    if e - s <= 4:
        return 'puntero'
    return 'binario'


def main(jp_dir, chs_dir, report, runs_json=None):
    jp_dir, chs_dir = Path(jp_dir), Path(chs_dir)
    rows, all_runs = [], {}
    for pj in sorted(p for p in jp_dir.rglob('*') if p.is_file() and p.name not in ('layout.xml', 'license_data.dat')):
        rel = pj.relative_to(jp_dir).as_posix()
        pc = chs_dir / rel
        if not pc.exists():
            continue
        a, b = pj.read_bytes(), pc.read_bytes()
        rs = runs_of(a, b)
        if not rs:
            continue
        kinds = Counter()
        detail = []
        for s, e in rs:
            k = classify(a, b, s, e)
            kinds[k] += e - s
            detail.append({'start': s, 'end': e, 'kind': k})
        all_runs[rel] = detail
        rows.append((rel, len(a), sum(e - s for s, e in rs), len(rs), kinds, sjis_ratio(a)))

    rows.sort(key=lambda r: -r[2])
    lines = ['# Diff JP vs CHS por archivo', '',
             f'Generado por `tools/src/diff_files.py`. Runs unidos con huecos <= {GAP} bytes.', '',
             '| Archivo | Tamaño | Bytes dif. | Runs | Texto | Punteros | Binario | SJIS% archivo JP |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for rel, size, nd, nr, k, ratio in rows:
        lines.append(f'| `{rel}` | {size:,} | {nd:,} | {nr:,} | {k["texto"]:,} | {k["puntero"]:,} | '
                     f'{k["binario"]:,} | {ratio:.0%} |')
    Path(report).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if runs_json:
        Path(runs_json).write_text(json.dumps(all_runs), encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
