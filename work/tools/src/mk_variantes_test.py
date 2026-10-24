"""Prueba de variantes del protagonista (issue #34): copia de dump/script.jsonl donde cada línea `$n` / `$l`
muestra su número de variante en vez del texto, para ver en el juego cuál elige según cara y personalidad.

Una racha = líneas consecutivas del mismo script con el mismo prefijo (`$n` o `$l`); se corta cada 8 (una línea del
guion = 8 variantes consecutivas, ver referencia/protagonistas.md §1). Las demás líneas quedan en japonés.
  `$n` → "$n: V3 (m shy)"     `$l` → "Partner: L3"     + "#<script>.<n° de bloque>" para ubicar la línea
Uso: mk_variantes_test.py <salida.jsonl>"""
import json, os, sys

WORK = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
PERS = ['m serious', 'm cool', 'm shy', 'm cheerful', 'f serious', 'f cool', 'f shy', 'f cheerful']


def main():
    out = sys.argv[1]
    rows = [json.loads(l) for l in open(os.path.join(WORK, 'dump', 'script.jsonl'), encoding='utf-8')]
    prev, pos, block, tagged = None, 0, 0, 0
    for r in rows:
        jp = r['jp']
        pre = jp[:2] if jp[:2] in ('$n', '$l') else None
        key = (r['script'], pre) if pre else None
        if key is None:
            prev = None
            continue
        if key != prev or pos == 8:      # racha nueva o bloque de 8 completo
            if key != prev:
                pos = 0
            pos = 0
            block += 1
        v = pos + 1
        pos += 1
        prev = key
        tag = f"#{r['script']}.{block}"
        r['en'] = (f"$n: V{v} ({PERS[v - 1]}) {tag}" if pre == '$n'
                   else f"Partner: L{v} (matches V{v}) {tag}")
        tagged += 1
    with open(out, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'{tagged} líneas marcadas, {block} bloques → {out}')


if __name__ == '__main__':
    main()
