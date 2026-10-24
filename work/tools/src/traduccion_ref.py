"""Referencias para traducir (carpeta traduccion/): refresca conteos, aplica correcciones y arma el glosario unificado.

Uso (desde la raíz del repo; solo stdlib, no necesita la ISO):
  python3 work/tools/src/traduccion_ref.py            # conteos + generado/ + reporte
  python3 work/tools/src/traduccion_ref.py --solo-reporte

Entradas curadas (se editan a mano; el script solo reescribe las columnas de conteo):
  traduccion/referencia/{lugares,facciones,naves,terminologia}.csv  → columna `apariciones`
  traduccion/referencia/frases_fijas.csv                            → columna `veces`
  traduccion/referencia/hablantes.csv                               → `lineas_script`, `lineas_snmsg` (+ cobertura)
  traduccion/referencia/correcciones.csv   erratas de work/glossary/glossary.csv (se aplican en generado/)
Salidas (no editar: se regeneran):
  traduccion/referencia/generado/{pilotos,unidades,armas,sistema}.csv   glosario con correcciones aplicadas
  traduccion/referencia/generado/glosario_unificado.tsv                 TODO término jp→en (lo usa lote.py)
  traduccion/referencia/generado/reporte.txt                            conflictos, cobertura, caracteres no codificables
Conteo: SCRIPT + SNMSG + BXCLIST + DEADMESS + EM, sin saltos de línea; variantes (`a|b`) sumadas sin solaparse.
"""
import argparse, collections, csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DUMP = ROOT / 'work' / 'dump'
GLOS = ROOT / 'work' / 'glossary'
REF = ROOT / 'traduccion' / 'referencia'
GEN = REF / 'generado'
TEXT_DUMPS = ['script', 'snmsg', 'bxclist', 'deadmess', 'em']
CURADOS = ['lugares', 'facciones', 'naves', 'terminologia']
SPEAKER = re.compile(r'^([^「（\n]{1,20})[「（]')
BODY = re.compile(r'^[^「（\n]{1,20}[「（](.*)[」）]$', re.S)
GLOS_FILES = {'pilotos': ('pilot',), 'unidades': ('unit',), 'armas': ('weapon',),
              'sistema': ('spirit', 'pilot_skill', 'unit_ability', 'part', 'ui')}


def flat(t: str) -> str:
    return t.replace('\n　', '').replace('\n', '')


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.DictReader(f)
        return list(r.fieldnames), list(r)


def write_csv(path: Path, fields: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)


def load_corpus():
    """Texto plano de todos los volcados + líneas por formato (para hablantes y frases)."""
    per = {}
    for name in TEXT_DUMPS:
        with open(DUMP / f'{name}.jsonl', encoding='utf-8') as f:
            per[name] = [json.loads(l)['jp'] for l in f if l.strip()]
    return '\n'.join(flat(t) for rows in per.values() for t in rows), per


def count_terms(text: str, variants: list[str]) -> int:
    """Suma las apariciones de todas las variantes sin contar dos veces un mismo tramo (la más larga primero)."""
    n = 0
    for v in sorted({v for v in variants if v}, key=len, reverse=True):
        n += text.count(v)
        text = text.replace(v, '\0')
    return n


def refresh_curados(text: str) -> list[str]:
    avisos = []
    for name in CURADOS:
        fields, rows = read_csv(REF / f'{name}.csv')
        for r in rows:
            r['apariciones'] = count_terms(text, [r['jp']] + r['variantes_jp'].split('|'))
            if r['apariciones'] == 0:
                avisos.append(f'{name}.csv: "{r["jp"]}" no aparece en los diálogos')
        write_csv(REF / f'{name}.csv', fields, rows)
    return avisos


def refresh_frases(per: dict, text: str):
    bodies = collections.Counter()
    for name in ('script', 'snmsg', 'bxclist', 'deadmess', 'em'):
        for t in per[name]:
            m = BODY.match(t)
            bodies[flat(m.group(1) if m else t)] += 1
    fields, rows = read_csv(REF / 'frases_fijas.csv')
    for r in rows:
        r['veces'] = {'linea': lambda: bodies[r['jp']], 'fragmento': lambda: text.count(r['jp'])}.get(r['modo'], lambda: '')()
    write_csv(REF / 'frases_fijas.csv', fields, rows)


# ───────── perfil de habla (medido en SCRIPT + SNMSG): pronombre, finales de frase, trato, formalidad ─────────
PRONOMBRES = ['俺様', 'オレ様', '俺', 'オレ', 'おれ', '僕', 'ボク', 'ぼく', 'わたくし', '私', 'わたし', 'あたし', 'アタシ', 'あたい',
              'うち', 'ウチ', '儂', 'わし', 'ワシ', '余', '我', '自分', 'おいどん', 'オイ', '拙者', '小生', 'ワイ', 'わい',
              'おいら', 'オイラ', '我輩', '吾輩']
PRON_RX = re.compile('(' + '|'.join(sorted(map(re.escape, PRONOMBRES), key=len, reverse=True)) + ')(?=[はがをにのもとだ達たちら、…！？ρσ]|$)')
# el primero que coincide gana: los más largos/específicos van primero
FINALES = ['だわさ', 'わよん', 'ですわ', 'だわ', 'わよ', 'わね', 'のよ', 'かしら', 'でござる', 'ござる', 'ございます', 'であります',
           'ごわす', 'ごわんど', 'ニャ', 'にゃ', 'っす', 'やで', 'やろ', 'へん', 'とね', 'じゃ', 'のう', 'ぜ', 'ぞ', 'さ', 'わ', 'よ',
           'ね', 'だ', 'な']
TRATO_RX = re.compile(r'([一-龥ァ-ヴー$a-zA-Z]{1,8}?)(君|さん|様|ちゃん|殿|先輩|大尉|少佐|中尉|少尉|艦長|博士|教授|長官|司令|隊長|提督|閣下)')
FORMAL_RX = re.compile(r'(です|ます|ました|でした|ません|でしょう|ください|ございます|ございません)$')
PUNCT = '！？!?…。、ρσ～ーっッ　 '
TEMPLE = {0: '0 弱気 débil', 1: '1 普通 normal', 2: '2 強気 fuerte', 3: '3 超強気 muy fuerte'}


def speech_profiles(per: dict) -> dict:
    """jp del hablante → 'pronombre · finales · trato · formal N%' (solo con ≥ 5 líneas)."""
    lines = collections.defaultdict(list)
    for name in ('script', 'snmsg'):
        for t in per[name]:
            if m := BODY.match(t):
                lines[SPEAKER.match(t).group(1)].append(flat(m.group(1)))
    out = {}
    for spk, ls in lines.items():
        if len(ls) < 5:
            continue
        pron, fin, trato, formal = collections.Counter(), collections.Counter(), collections.Counter(), 0
        for t in ls:
            pron.update(m.group(1) for m in PRON_RX.finditer(t))
            trato.update(m.group(0) for m in TRATO_RX.finditer(t))
            formal += bool(FORMAL_RX.search(t.rstrip(PUNCT)))
            for seg in re.split(r'[。！？!?ρσ]+', t):
                seg = seg.rstrip(PUNCT)
                f = next((f for f in FINALES if seg.endswith(f)), None)
                if f:
                    fin[f] += 1
        p = '/'.join(k for k, _ in pron.most_common(2)) or '—'
        out[spk] = (f'{p} · {"/".join(k for k, _ in fin.most_common(4)) or "—"} · '
                    f'trato: {", ".join(k for k, _ in trato.most_common(3)) or "—"} · formal {round(100 * formal / len(ls))}%')
    return out


def pilot_temple(g: list[dict]) -> dict:
    """Nombre inglés y jp del glosario → personalidad de combate de PILOT.BIN (+0x6A; afecta al Will)."""
    with open(DUMP / 'pilot.jsonl', encoding='utf-8') as f:
        nat = {}
        for l in f:
            p = json.loads(l)
            nat.setdefault(norm_name(p['full']), p['nature'])
    out = {}
    for r in g:
        if r['category'] != 'pilot':
            continue
        for j in (r.get('jp_game', ''), r['jp']):
            n = norm_name(j) if j else ''
            v = nat.get(n)
            if v is None and len(n) >= 4:   # PILOT.BIN corta a 20 bytes
                v = next((x for k, x in nat.items() if n.startswith(k) and len(k) >= 4), None)
            if v is not None:
                out.setdefault(r['en_final'], TEMPLE.get(v, str(v)))
                out.setdefault('jp:' + r['jp'], TEMPLE.get(v, str(v)))
                break
    return out


def temple_for(r: dict, temple: dict) -> str:
    """Por nombre completo; si no, por la etiqueta japonesa como parte del nombre (十三 → 浪花十三), solo si es única."""
    if r['nombre_completo'] in temple:
        return temple[r['nombre_completo']]
    if r['jp'].startswith('$') or len(r['jp']) < 2:
        return ''
    parts = {k[3:]: v for k, v in temple.items() if k.startswith('jp:')}
    cands = {v for j, v in parts.items() if r['jp'] in re.split('[・＝= ]', j)}
    if not cands:
        cands = {v for j, v in parts.items() if r['jp'] in j}
    return cands.pop() if len(cands) == 1 else ''


def norm_name(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(?<=[ァ-ヴー])-', 'ー', s).replace('=', '・').replace('＝', '・')
    return re.sub(r'\s+', '', s)


def refresh_hablantes(per: dict) -> list[str]:
    cs = collections.Counter(m.group(1) for t in per['script'] if (m := SPEAKER.match(t)))
    with open(DUMP / 'snmsg.jsonl', encoding='utf-8') as f:
        cm = collections.Counter(s for l in f if (s := json.loads(l).get('speaker')))
    fields, rows = read_csv(REF / 'hablantes.csv')
    for col in ('habla_jp', 'temperamento'):
        if col not in fields:
            fields.append(col)
    habla = speech_profiles(per)
    temple = pilot_temple(glossary_corrected()[0])
    known = set()
    for r in rows:
        r['lineas_script'], r['lineas_snmsg'] = cs[r['jp']], cm[r['jp']]
        r['habla_jp'] = habla.get(r['jp'], '')
        r['temperamento'] = temple_for(r, temple)
        known.add(r['jp'])
    write_csv(REF / 'hablantes.csv', fields, rows)
    faltan = [(k, cs[k] + cm[k]) for k in (set(cs) | set(cm)) - known]
    return [f'hablantes.csv: falta "{k}" ({n} líneas)' for k, n in sorted(faltan, key=lambda x: -x[1])]


def glossary_corrected():
    _, g = read_csv(GLOS / 'glossary.csv')
    _, corr = read_csv(REF / 'correcciones.csv')
    fix = {(c['category'], c['jp']): c for c in corr}
    usadas = set()
    for r in g:
        c = fix.get((r['category'], r['jp']))
        r['correccion'] = ''
        if c:
            usadas.add((c['category'], c['jp']))
            if r['en_final'] != c['en_glosario']:
                r['correccion'] = f'OJO: el glosario ya dice "{r["en_final"]}"'
            else:
                r['correccion'] = f'antes "{r["en_final"]}": {c["motivo"]}'
            r['en_final'] = c['en_corregido']
    no_usadas = [f'correcciones.csv: ({k[0]}, {k[1]}) no está en glossary.csv' for k in fix if k not in usadas]
    return g, no_usadas


def write_generated(g: list[dict]):
    cols = ['category', 'series', 'jp', 'en', 'en_short', 'status', 'correccion', 'notes']
    for fname, cats in GLOS_FILES.items():
        rows = [{'category': r['category'], 'series': r['series'], 'jp': r['jp'], 'en': r['en_final'],
                 'en_short': r['en_short'], 'status': r['status'], 'correccion': r['correccion'], 'notes': r['notes']}
                for r in g if r['category'] in cats]
        write_csv(GEN / f'{fname}.csv', cols, rows)


def unified(g: list[dict]) -> list[tuple]:
    """(jp, en, en_corto, tipo, serie, archivo) de todas las fuentes. El orden decide qué gana al buscar."""
    out = []
    _, hab = read_csv(REF / 'hablantes.csv')
    for r in hab:
        if not r['jp'].startswith('$'):
            out.append((r['jp'], r['en'], '', 'hablante', r['serie'], 'hablantes.csv'))
    for name in CURADOS:
        _, rows = read_csv(REF / f'{name}.csv')
        for r in rows:
            for v in [r['jp']] + [v for v in r['variantes_jp'].split('|') if v]:
                out.append((v, r['en'], '', f'{name}:{r["tipo"]}', r['serie'], f'{name}.csv'))
    _, mis = read_csv(REF / 'misiones.csv')
    for r in mis:
        out.append((r['jp'], r['en'], r['en_corto'], 'mision', '', 'misiones.csv'))
    for r in g:
        f = next(k for k, v in GLOS_FILES.items() if r['category'] in v)
        out.append((r['jp'], r['en_final'], r['en_short'], r['category'], r['series'], f'generado/{f}.csv'))
        if r.get('jp_game') and r['jp_game'] != r['jp']:
            out.append((r['jp_game'], r['en_final'], r['en_short'], r['category'], r['series'], f'generado/{f}.csv'))
    return out


def report(uni: list[tuple], avisos: list[str]) -> list[str]:
    lines = []
    by_jp = collections.defaultdict(set)
    for jp, en, _, tipo, _, src in uni:
        by_jp[jp].add((en, src))
    def real_conflict(v):
        ens = {e.lower() for e, _ in v}
        if len(ens) < 2:
            return False
        # etiqueta de hablante contenida en el nombre completo (Karius / Karius Otto): no es conflicto
        labels = {e.lower() for e, s in v if s == 'hablantes.csv'}
        return not any(all(lab in e for e in ens) for lab in labels)
    conf = sorted((jp, v) for jp, v in by_jp.items() if real_conflict(v))
    lines.append(f'## Conflictos: mismo JP con distinto EN según el archivo ({len(conf)})')
    lines.append('Sin distinguir mayúsculas. Normales si el JP es ambiguo o es etiqueta vs. nombre completo; revisar los demás.')
    for jp, v in conf:
        lines.append(f'  {jp}: ' + ' | '.join(f'{e} ({s})' for e, s in sorted(v)))
    bad = []
    for jp, en, *_rest in uni:
        try:
            en.encode('cp932')
        except UnicodeEncodeError:
            bad.append(f'  {jp} → {en}')
    lines.append(f'\n## EN con caracteres que la fuente del juego no codifica (cp932) ({len(bad)})')
    lines += sorted(set(bad))
    lines.append(f'\n## Avisos ({len(avisos)})')
    lines += [f'  {a}' for a in avisos]
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--solo-reporte', action='store_true', help='no reescribe conteos: solo generado/ y reporte')
    a = ap.parse_args(argv)
    avisos = []
    if not a.solo_reporte:
        text, per = load_corpus()
        avisos += refresh_curados(text)
        refresh_frases(per, text)
        avisos += refresh_hablantes(per)
    g, no_usadas = glossary_corrected()
    avisos += no_usadas
    write_generated(g)
    uni = unified(g)
    with open(GEN / 'glosario_unificado.tsv', 'w', encoding='utf-8') as f:
        f.write('jp\ten\ten_corto\ttipo\tserie\tarchivo\n')
        f.writelines('\t'.join(r) + '\n' for r in uni)
    rep = report(uni, avisos)
    (GEN / 'reporte.txt').write_text('\n'.join(rep) + '\n', encoding='utf-8')
    n_conf = next(l for l in rep if l.startswith('## Conflictos'))
    print(f'glosario_unificado.tsv: {len(uni)} términos · {n_conf[3:]} · avisos: {len(avisos)} → {GEN / "reporte.txt"}')


if __name__ == '__main__':
    sys.exit(main())
