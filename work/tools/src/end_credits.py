"""Créditos finales (overlay END, `OVL/END_GRP.BIN`): extrae, clasifica y cruza con las fuentes del proyecto (#11).

No necesita la ISO: lee el inventario versionado `dump/ovl_strings.jsonl` (filas `file: END`).
- Texto real: los strings con referencia `ptr` (bloque 0x0004–0x30BC del overlay). El resto de las filas de END son bytes
  de código (desde 0x3100) que parecen SJIS: se cuentan y se descartan.
- Tabla de créditos: palabras de 32 bits con paso 8 desde el offset 0x5C0C; el orden de la tabla es el orden en pantalla
  (columna `orden`). Un mismo string puede aparecer varias veces (p. ej. 寺田 貴信: productor y director general).
- `en_sugerido` sale SOLO de fuentes ya existentes (nada inventado): roles de `traduccion/referencia/creditos_y_canciones.md`,
  series de `series.csv`, personajes de `decisiones.csv` / `glossary.csv` / `hablantes.csv` / fichas DC, seiyuu del campo
  "voz" de las fichas DC (`translation/dc_en.jsonl`). Lo que no está en ninguna queda vacío.
Uso: end_credits.py → dump/end_credits.csv + resumen
"""
import collections, csv, json, os, re, unicodedata

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REPO = os.path.dirname(WORK)
TABLE = 0x5C0C          # primera palabra de la tabla de créditos (paso 8)
COMPANY_ROLES = {'制作協力会社', '録音スタジオ', '開発', '製作・販売'}
EMPRESA = re.compile(r'株式会社|有限会社|（株）|プロダクション|スタジオ|ホール|グループ|スクール|ソフト')


def norm(s):
    """Clave de búsqueda: NFKC (medio ancho → ancho completo, Ｆ → F), separadores ＝ ・ → =, guion largo unificado."""
    s = unicodedata.normalize('NFKC', s).strip()
    s = re.sub(r'[=・]', '=', s)
    s = re.sub(r'(?<=[゠-ヿ])-', 'ー', s)
    return re.sub(r'\s+', '', s)


def load_sources():
    roles, series, chars, voices = {}, {}, {}, {}
    # Roles: tablas "| JP | EN |" de la guía de créditos; "A / B" se reparte si ambos lados tienen la misma cantidad
    guia = open(os.path.join(REPO, 'traduccion', 'referencia', 'creditos_y_canciones.md'), encoding='utf-8').read()
    for jp, en in re.findall(r'^\| ([^|]+?) \| ([^|]+?) \|$', guia, re.M):
        js, es = jp.split(' / '), en.split(' / ')
        for j, e in (zip(js, es) if len(js) == len(es) else [(jp, en)]):
            roles[norm(j)] = e.strip()
    # Nombres de staff que la guía ya romanizó: `寺田　貴信` → *Takanobu Terada*
    staff = {norm(j): e for j, e in re.findall(r'`([^`]+)` → \*([^*]+)\*', guia)}
    for r in csv.DictReader(open(os.path.join(REPO, 'traduccion', 'referencia', 'series.csv'), encoding='utf-8')):
        series[norm(r['jp'])] = r['en']
    # Personajes, de menor a mayor prioridad (la última escritura gana): fichas DC < hablantes < glosario < decisiones
    for l in open(os.path.join(WORK, 'translation', 'dc_en.jsonl'), encoding='utf-8'):
        d = json.loads(l)
        f, en = [x['text'] for x in d['fields']], d['en']
        if len(f) > 3 and len(en) > 3:
            chars[norm(re.sub(r'（.*）', '', f[0]))] = (en[0], 'DC')
            series.setdefault(norm(f[2]), en[2])
            voices[norm(f[3])] = en[3].strip()
            for j, e in zip(re.split('[・、]', f[3]), re.split(r' / |, | & | and ', en[3])):
                voices.setdefault(norm(j), e.strip())
    for r in csv.DictReader(open(os.path.join(REPO, 'traduccion', 'referencia', 'hablantes.csv'), encoding='utf-8')):
        if r['nombre_completo'] and not r['jp'].startswith('$'):
            chars[norm(r['jp'])] = (r['nombre_completo'], 'hablantes')
    for name in ('glossary.csv', 'decisiones.csv'):
        for r in csv.DictReader(open(os.path.join(WORK, 'glossary', name), encoding='utf-8')):
            if r['category'] == 'pilot' and r['en_final']:
                chars[norm(r['jp'])] = (r['en_final'], name.split('.')[0])
    return roles, series, chars, voices, staff


def main():
    rows = [json.loads(l) for l in open(os.path.join(WORK, 'dump', 'ovl_strings.jsonl'), encoding='utf-8')]
    end = [r for r in rows if r['file'] == 'END']
    text = [r for r in end if any(x.startswith('ptr@') for x in r['refs'])]
    roles, series, chars, voices, staff = load_sources()

    out, section = [], ''
    for i, r in enumerate(text):
        jp = r['jp']
        body = jp[1:] if jp.startswith('％') else jp
        orden = sorted((int(x.split('@')[1], 16) - TABLE) // 8 for x in r['refs'] if x.startswith('ptr@'))
        en, src, notes = '', '', []
        if re.fullmatch(r'[Ａ-Ｚ　]+', jp):
            tipo, en, src = 'fin', unicodedata.normalize('NFKC', jp), 'ya en inglés (ancho completo)'
        elif jp.lstrip('　').startswith('＃'):
            tipo, notes = 'espaciador', ['cierre del reparto: columna vacía + "(順不同）" (en no particular order)']
        elif not jp.startswith('％') and jp.startswith('「') and not jp.endswith('原作'):
            tipo = 'serie'
            parts = re.findall(r'「([^」]+)」', jp)
            hits = [series.get(norm(p), '') for p in parts]
            en = ' / '.join(hits) if all(hits) else ''
            src = 'series.csv/DC' if en else ''
            if not en:
                notes.append('falta en series.csv: ' + ', '.join(p for p, h in zip(parts, hits) if not h))
        elif not jp.startswith('％'):
            tipo, section = 'rol', jp
            en = roles.get(norm(jp), '')
            src = 'creditos_y_canciones.md' if en else ''
        elif '＃' in jp:
            tipo = 'reparto'
            ch, vo = body.split('＃', 1)
            che, chs = chars.get(norm(ch), ('', ''))
            vos = [voices.get(norm(v), '') for v in re.split('・', vo.strip())]
            voe = voices.get(norm(vo), '') or (' / '.join(vos) if all(vos) else '')
            if che and voe:
                en, src = f'％{che}＃{voe}', f'{chs}+DC(voz)'
            notes += [] if che else [f'personaje sin fuente: {ch}']
            notes += [] if voe else [f'seiyuu sin fuente: {vo.strip()}']
            if re.search(r'[｡-ﾟ]', jp):
                notes.append('el japonés pasó a medio ancho para entrar en la columna')
        else:
            tipo = 'empresa' if section in COMPANY_ROLES or (EMPRESA.search(body) and '　' not in body) else 'staff'
            key = norm(body)
            if key in staff:
                en, src = '％' + staff[key], 'creditos_y_canciones.md'
            if '（' in body:
                notes.append('empresa entre paréntesis')
        if jp != jp.rstrip(' '):
            notes.append('espacios ASCII al final')
        out.append({'id': i, 'off': f"{r['off']:#06x}", 'addr': r['addr'], 'orden': ' '.join(map(str, orden)),
                    'seccion': section, 'tipo': tipo, 'jp': jp, 'en_sugerido': en, 'fuente': src,
                    'bytes': r['bytes'], 'room': r['room'], 'notas': '; '.join(notes)})

    dst = os.path.join(WORK, 'dump', 'end_credits.csv')
    with open(dst, 'w', encoding='utf-8', newline='') as fo:
        w = csv.DictWriter(fo, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    n_tab = sum(len(o['orden'].split()) for o in out)
    print(f'END: {len(end)} candidatos → {len(text)} strings de créditos (+{len(end) - len(text)} bytes de código '
          f'descartados); tabla 0x{TABLE:X}: {n_tab} renglones en pantalla → {dst}')
    by = collections.defaultdict(lambda: [0, 0])
    for o in out:
        by[o['tipo']][0] += 1
        by[o['tipo']][1] += bool(o['en_sugerido'])
    for t, (n, ok) in sorted(by.items(), key=lambda x: -x[1][0]):
        print(f'  {t:11} {n:4}  con en_sugerido: {ok:4}')
    jp_b = sum(o['bytes'] + 1 for o in out)
    con = [o for o in out if o['en_sugerido']]
    en_b = sum(len(o['en_sugerido'].encode('cp932')) + 1 for o in con)
    print(f"  bytes JP del bloque de texto: {jp_b}; filas con en_sugerido: JP {sum(o['bytes'] + 1 for o in con)} B "
          f"→ EN {en_b} B (ASCII = 1 B; ％/＃ = 2 B)")


if __name__ == '__main__':
    main()
