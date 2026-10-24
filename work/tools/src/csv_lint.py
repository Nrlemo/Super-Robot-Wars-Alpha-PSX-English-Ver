"""Control de los CSV/TSV versionados (glosario, referencias, decisiones). Solo stdlib, no necesita la ISO.

Uso (desde la raíz del repo): python3 work/tools/src/csv_lint.py [archivo …]
  Sin argumentos revisa todos los *.csv y *.tsv que sigue git.
  - Todos: UTF-8, encabezado sin columnas vacías ni repetidas y cada fila con tantas columnas como el encabezado
    (una coma sin comillas en `notes` corre las columnas y trunca la nota en silencio).
  - glossary.csv y decisiones.csv: (category, jp) único, en_final no vacío y en_final/en_short codificables en cp932
    (la fuente del juego no tiene otros caracteres). glossary.csv además: status conocido.
Sale con 1 si hay algún error.
"""
import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATUS = {'official', 'source', 'manual', 'proposed', 'reviewed'}
KEYED = {'work/glossary/glossary.csv', 'work/glossary/decisiones.csv'}


def tracked() -> list[str]:
    out = subprocess.run(['git', 'ls-files', '*.csv', '*.tsv'], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.split()


def delimiter(rel: str, head: str) -> str:
    """TSV: tabulador. CSV: coma, salvo que el encabezado use ';' (respuestas de la investigación externa)."""
    if rel.endswith('.tsv'):
        return '\t'
    return ';' if head.count(';') > head.count(',') else ','


def lint(rel: str) -> list[str]:
    path = ROOT / rel
    try:
        text = path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError as e:
        return [f'{rel}: no es UTF-8 ({e})']
    lines = text.splitlines()
    if not lines:
        return [f'{rel}: vacío']
    rows = list(csv.reader(lines, delimiter=delimiter(rel, lines[0])))
    head, errs = rows[0], []
    if any(not h.strip() for h in head) or len(set(head)) != len(head):
        errs.append(f'{rel}: encabezado con columnas vacías o repetidas: {head}')
    for n, r in enumerate(rows[1:], 2):
        if r and len(r) != len(head):
            errs.append(f'{rel}:{n}: {len(r)} columnas (encabezado: {len(head)}) → ¿coma sin comillas? {r[:3]}')
    if rel in KEYED and not errs:
        errs += lint_terms(rel, [dict(zip(head, r)) for r in rows[1:] if r])
    return errs


def lint_terms(rel: str, rows: list[dict]) -> list[str]:
    errs = []
    dup = [k for k, c in Counter((r['category'], r['jp']) for r in rows).items() if c > 1]
    errs += [f'{rel}: (category, jp) repetido: {k}' for k in dup]
    for r in rows:
        if not r['en_final'].strip():
            errs.append(f'{rel}: {r["category"]} {r["jp"]}: en_final vacío')
        for col in ('en_final', 'en_short'):
            try:
                r.get(col, '').encode('cp932')
            except UnicodeEncodeError:
                errs.append(f'{rel}: {r["category"]} {r["jp"]}: {col} {r[col]!r} no se codifica en cp932')
        if 'status' in r and r['status'] not in STATUS:
            errs.append(f'{rel}: {r["category"]} {r["jp"]}: status desconocido {r["status"]!r}')
    return errs


def main(argv: list[str]) -> int:
    files = argv or tracked()
    errs = [e for f in files for e in lint(f)]
    for e in errs:
        print('ERROR', e)
    print(f'{len(files)} archivos · {len(errs)} errores')
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
