#!/usr/bin/env python3
"""Candidatos a re-fluir saltos de línea (issue #266). SOLO LISTA: no modifica los JSONL.

Regla: una línea que termina en . ! ? ... o … es corte obligatorio (tanda 1: solo saltos a mitad de frase); dentro de cada
tramo entre cortes se unen las líneas y se re-parten con el ajuste codicioso de check_text.wrap.
Es candidato si baja el número de líneas del tramo (tramo = una o más líneas consecutivas sin corte obligatorio).

Uso: python3 reflow_candidates.py [script|snmsg|em|deadmess] [--out work/logs/reflow_script.tsv]
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_text as ct

HARD_MID = re.compile(r'([.!?…]|\.\.\.)["\')」』）]*\s*$')   # fin de frase = corte obligatorio; solo se unen saltos a mitad de frase

HARD_ELLIPSIS = re.compile(r'(\.\.\.|…)["\')」』）]*\s*$')   # tanda 2: solo la pausa con puntos suspensivos es corte
HARD = HARD_MID


def segments(lines):
    seg, out = [], []
    for ln in lines:
        seg.append(ln)
        if HARD.search(ln):
            out.append(seg)
            seg = []
    if seg:
        out.append(seg)
    return out


def reflow(en, width, kana_px):
    new = []
    for seg in segments(en.split('\n')):
        new.extend(ct.wrap(' '.join(s.strip() for s in seg), width, kana_px))
    return new


def reflow_text(fmt, d, names=None, width=None, hard=None):
    """Nuevo `en` de la fila `d` con los saltos a mitad de frase unidos, o None si no hay cambio. Reutilizable (lote.py)."""
    global HARD
    f = ct.FORMATS[fmt]
    en = d.get('en')
    if fmt == 'script' and d.get('sub') in (1, 2):   # op 0x80: cada línea es una opción de decisión, no se unen
        return None
    if ct.is_choice(d.get('jp')):                     # decisión de mapa en SNMSG: ídem
        return None
    if not en or '\n' not in en or any(len(x) == 0 for x in en.split('\n')):
        return None
    w = width or f.line_px
    if fmt == 'deadmess':       # el juego antepone el nombre: se reserva en todas las líneas (conservador)
        nm = (names or {}).get(d['pilot'], '')
        w -= (ct.line_px(nm, 12) if nm else 0) + ct.line_px(ct.DEADMESS_PREFIX, 12)
    old_hard, HARD = HARD, (hard or HARD)
    try:
        new = reflow(en, w, f.kana_px)
    finally:
        HARD = old_hard
    return '\n'.join(new) if len(new) < len(en.split('\n')) and len(new) <= f.max_lines else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fmt', nargs='?', default='script')
    ap.add_argument('--out')
    ap.add_argument('--apply', action='store_true', help='reescribe el campo en de los candidatos en work/dump/<fmt>.jsonl')
    ap.add_argument('--tanda2', action='store_true', help='solo los puntos suspensivos son corte obligatorio (une también saltos tras . ! ?)')
    ap.add_argument('--width', type=int, help='ancho máximo en px (por defecto el del formato)')
    a = ap.parse_args()
    global HARD
    if a.tanda2:
        HARD = HARD_ELLIPSIS
    f = ct.FORMATS[a.fmt]
    path = ct.WORK / 'dump' / f.file
    out = Path(a.out or ct.WORK / 'logs' / f'reflow_{a.fmt}.tsv')
    out.parent.mkdir(parents=True, exist_ok=True)
    names = ct.pilot_short_names() if a.fmt == 'deadmess' else {}
    tot = cand = saved = 0
    rows, outl = [], []
    for n, l in enumerate(open(path, encoding='utf-8'), 1):
        d = json.loads(l)
        outl.append(d)
        en = d.get('en')
        if not en or '\n' not in en:
            continue
        tot += 1
        old = en.split('\n')
        if any(len(x) == 0 for x in old):           # líneas vacías: no tocar
            continue
        if (a.fmt == 'script' and d.get('sub') in (1, 2)) or ct.is_choice(d.get('jp')):   # opciones de decisión: no se unen
            continue
        width = a.width or f.line_px
        if a.fmt == 'deadmess':       # el juego antepone nombre「 y cierra con 」: se reserva en todas las líneas (conservador)
            nm = names.get(d['pilot'], '')
            width -= (ct.line_px(nm, 12) if nm else 0) + ct.line_px(ct.DEADMESS_PREFIX, 12)
        new = reflow(en, width, f.kana_px)
        if len(new) > f.max_lines:
            continue
        if len(new) < len(old):
            cand += 1
            d['en'] = '\n'.join(new)
            saved += len(old) - len(new)
            ident = d.get('id') or f"{d.get('script')}/{d.get('inst')}/{d.get('line')}/{d.get('sub')}"
            rows.append((n, ident, len(old), len(new), en.replace('\n', ' ⏎ '), ' ⏎ '.join(new)))
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('jsonl_line\tid\told_lines\tnew_lines\told\tnew\n')
        for r in rows:
            fh.write('\t'.join(map(str, r)) + '\n')
    if a.apply:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.writelines(json.dumps(d, ensure_ascii=False) + '\n' for d in outl)
    print(f'{a.fmt}: {tot} con saltos, {cand} candidatos, {saved} líneas menos → {out}')


if __name__ == '__main__':
    main()
