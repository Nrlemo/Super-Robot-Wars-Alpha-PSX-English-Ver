"""Lista para revisar: textos de menú que quedaron en forma corta (o en japonés) por falta de lugar.

Lee build/menus/report.csv (de ovl_patch.py) y translation/menus_en.jsonl → translation/menus_acortados.csv
(file, addr, jp, en, usado, motivo, refs). Uso: menus_short_list.py
"""
import collections, csv, json, os

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
rows = {(r['file'], r['addr']): r for r in map(json.loads, open(os.path.join(WORK, 'translation', 'menus_en.jsonl'),
                                                                  encoding='utf-8'))}
out = []
for r in csv.DictReader(open(os.path.join(WORK, 'build', 'menus', 'report.csv'), encoding='utf-8')):
    if r['short'] == 'True' or r['how'] == 'sin cambio':
        j = rows[(r['file'], r['addr'])]
        out.append({'file': r['file'], 'addr': r['addr'], 'jp': j['jp'], 'en': j['en'],
                    'usado': r['used'] or '(japonés)',
                    'motivo': 'fragmento sin lugar' if r['how'] == 'sin cambio' else 'sin lugar para el completo',
                    'refs': r['refs']})
dst = os.path.join(WORK, 'translation', 'menus_acortados.csv')
with open(dst, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, ['file', 'addr', 'jp', 'en', 'usado', 'motivo', 'refs'])
    w.writeheader()
    w.writerows(out)
print(len(out), 'filas →', dst, dict(collections.Counter(o['file'] for o in out)))
