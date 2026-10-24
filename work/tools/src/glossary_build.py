"""Arma el glosario canónico JP→EN a partir de las páginas guardadas en info/.

Fuentes (convertidas a texto en glossary/src_txt/ por este mismo script):
  Character List / Unit List (Akurasu)  → pilotos y unidades, por serie
  Spirit, Pilot Ability, Unit Ability, OP Parts (Akurasu) → espíritus, habilidades, partes
  Move List (GameFAQs, Chiche)          → términos de menú / estadísticas
Armas: nombres reales del juego desde dump/robot.jsonl (robot_raf.py); inglés de weapons_en.csv + weapons_review.csv.
Unidades: inglés de units_en.csv (486 unidades del juego). Decisiones del responsable: decisiones.csv (ganan siempre).\nCruza cada término con el juego: nombres de PILOT.BIN y apariciones en dump/snmsg.jsonl.
Nombres oficiales en inglés: páginas de Akurasu (OGs, T, 30, V, X), cacheadas en glossary/web/ (--web las reparsea).
Sale: glossary/glossary.csv  (las columnas en_final / notes se editan a mano y se conservan al regenerar).
"""
import csv, glob, json, os, re, sys, unicodedata

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INFO = os.path.join(WORK, '..', 'info')
OUT = os.path.join(WORK, 'glossary')
TXT = os.path.join(OUT, 'src_txt')

FIELDS = ['category', 'series', 'jp', 'en_final', 'en_short', 'status', 'en_source', 'source', 'en_official', 'in_pilot_bin', 'jp_game',
          'snmsg_hits', 'notes']

# Prioridad de las localizaciones oficiales (CLAUDE.md §6: OG primero), páginas de Akurasu en glossary/web/
OFFICIAL_ORDER = ['ogs', 'T', '30', 'V', 'X']

# Términos sin nombre oficial en ninguna entrega en inglés: propuesta propia (status = proposed, revisar)
PROPOSED = {
    ('spirit', '自爆'): 'Self-Destruct', ('spirit', '挑発'): 'Taunt', ('spirit', '隠れ身'): 'Stealth',
    ('spirit', '奇襲'): 'Ambush', ('spirit', '激闘'): 'Fury', ('spirit', '奇跡'): 'Miracle',
    ('spirit', '捨て身'): 'Sacrifice', ('spirit', '復活'): 'Revive',
    ('unit_ability', '換装'): 'Reequip',
    # interfaz: vocabulario de las entregas en inglés recientes (T/30), no extraído de páginas
    ('ui', '機動力'): 'Move', ('ui', '運動性'): 'Mobility', ('ui', '機甲'): 'Armor', ('ui', '限界'): 'Limit',
    ('ui', '修理費'): 'Repair Cost', ('ui', 'タイプ'): 'Type', ('ui', 'サイズ'): 'Size', ('ui', '地形'): 'Terrain',
    ('ui', '武器名'): 'Weapon', ('ui', '攻撃力'): 'Attack', ('ui', '射程'): 'Range', ('ui', '命中'): 'Accuracy',
    ('ui', '弾薬'): 'Ammo', ('ui', '地形適応'): 'Terrain', ('ui', '必要気力'): 'Will Req.', ('ui', '消費EN'): 'EN Cost',
    ('ui', '必要技能'): 'Skill Req.', ('ui', 'クリティカル補正'): 'Critical', ('ui', '撃墜数'): 'Kills',
    ('ui', 'ユニット能力'): 'Unit Stats', ('ui', 'パイロット能力'): 'Pilot Stats', ('ui', '武器性能'): 'Weapon Stats',
    ('ui', '空'): 'Air', ('ui', '陸'): 'Land', ('ui', '海'): 'Sea', ('ui', '宇'): 'Space',
}
# grafía del juego (PILOT.BIN) para nombres que la búsqueda por similitud no resuelve
PILOT_GAME_ALIASES = {'ブリタイ・クリダニク': 'ブリタイ7018', 'エキセドル・フォルモ': '4970・エキセドル',
                      'カムジン・クラヴシェラ': 'カムジン03850', 'ミオ・サスガ': 'サスガ・ミオ', 'EVA量産機': 'エヴァ量産機'}
ALIASES = {'ひらめき': '閃き', 'イナーシャルキャンセラー': 'イナーシャル・キャンセラー'}


def html_to_txt():
    from bs4 import BeautifulSoup
    os.makedirs(TXT, exist_ok=True)
    for f in glob.glob(os.path.join(INFO, '*.html')):
        s = BeautifulSoup(open(f, encoding='utf-8', errors='replace').read(), 'lxml')
        for t in s(['script', 'style', 'nav', 'footer', 'header']):
            t.decompose()
        main = s.find(id='mw-content-text') or s.find(id='faqtext') or s.body
        for tr in main.find_all('tr'):  # filas de tabla → una línea separada por tabs
            cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
            tr.replace_with(s.new_string('\n' + '\t'.join(cells) + '\n'))
        txt = re.sub(r'\n\s*\n+', '\n', main.get_text('\n'))
        name = os.path.basename(f)[:-5]
        name = re.sub(r' - (Akurasu Wiki|PlayStation.*)', '', name)
        name = name.replace('Super Robot Wars_Alpha_', '').replace('Super Robot Taisen Alpha - ', '')
        open(os.path.join(TXT, name + '.txt'), 'w').write(txt)


OFFICIAL_PAGES = [f'spirit_{g}:Super_Robot_Wars/{g}/Spirit_Commands' for g in ('OGs', 'T', '30', 'V', 'X')] + [
    f'{g.lower() if g == "OGs" else g}_{p}:Super_Robot_Wars/{g}/{p}' for g in ('OGs', 'T', '30') for p in ('Pilot_Skills', 'Parts')]


def fetch_official():
    """Descarga las páginas de Akurasu con nombres oficiales en inglés y arma web/official_terms.json."""
    import urllib.request
    from bs4 import BeautifulSoup
    web = os.path.join(OUT, 'web')
    os.makedirs(web, exist_ok=True)
    terms = {}
    for spec in OFFICIAL_PAGES:
        name, page = spec.split(':', 1)
        path = os.path.join(web, name + '.html')
        if not os.path.exists(path):
            req = urllib.request.Request('https://akurasu.net/wiki/' + page, headers={'User-Agent': 'Mozilla/5.0'})
            open(path, 'wb').write(urllib.request.urlopen(req, timeout=30).read())
        soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
        for tr in soup.select('table tr'):
            c = [x.get_text(' ', strip=True) for x in tr.find_all(['td', 'th'])]
            for en, jp in zip(c, c[1:]):  # celdas vecinas "English | 日本語"
                if (re.fullmatch(r"[A-Za-z0-9\-.'’ ()/&+]+", en)
                        and re.fullmatch(r'[\u3040-\u9fff\uff00-\uffefA-Za-z0-9ー・（）()/\-＝= 　]+', jp)
                        and re.search(r'[\u3040-\u9fff]', jp)):
                    terms.setdefault(jp.strip(), {}).setdefault(en.strip(), set()).add(name)
    out = {k: {e: sorted(v) for e, v in d.items()} for k, d in terms.items()}
    json.dump(out, open(os.path.join(web, 'official_terms.json'), 'w'), ensure_ascii=False, indent=0)


def norm(s):
    """Forma comparable: NFKC, guiones/iguales de medio ancho → ー / ・, sin espacios."""
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(?<=[ァ-ヴー])-', 'ー', s).replace('=', '・').replace('＝', '・')
    return re.sub(r'\s+', '', s)


def lines(name):
    return open(os.path.join(TXT, name + '.txt'), encoding='utf-8').read().splitlines()


def is_jp(s):
    return bool(re.search(r'[぀-ヿ一-鿿ｦ-ﾟ]', s))


def series_tables(name, category):
    """Tablas 'Japanese Name / English Name' agrupadas bajo el título de la serie."""
    out, series, prev = [], '', ''
    for ln in lines(name):
        cells = ln.split('\t')
        if cells[1:3] == ['Japanese Name', 'English Name']:
            series = prev.strip()
        elif len(cells) >= 3 and series and is_jp(cells[1]):
            note = 'no controlable (★)' if cells[0] == '★' else ''
            out.append(dict(category=category, series=series, jp=cells[1].strip(), en_source=cells[2].strip(),
                            source='akurasu:' + name, notes=note))
        prev = ln
    return out


def simple_table(name, category, jp_col, en_col):
    out = []
    for ln in lines(name):
        c = ln.split('\t')
        if len(c) > max(jp_col, en_col) and is_jp(c[jp_col]) and not is_jp(c[en_col]) and c[en_col].strip():
            out.append(dict(category=category, series='', jp=c[jp_col].strip(), en_source=c[en_col].strip(),
                            source='akurasu:' + name, notes=''))
    return out


def move_list_terms():
    """Líneas 'JP - English' de la guía de Chiche (términos de interfaz, partes, habilidades)."""
    out, pending, section = [], None, 'ui'
    sect = {'強化パーツ': 'part', '特殊能力': 'unit_ability', '情神コマンド': 'spirit', '特殊技能': 'pilot_skill'}
    for ln in lines('Move List'):
        s = ln.strip()
        m = re.match(r'^(\S[^-]*?)\s+-\s*(.*)$', s)
        if pending and s and not is_jp(s):
            out.append(dict(category=section, series='', jp=pending, en_source=re.sub(r'\s*\(.*', '', s.split('\t')[0]),
                            source='gamefaqs:Move List', notes=s))
            pending = None
            continue
        if m and is_jp(m.group(1)):
            jp, en = m.group(1).strip(), m.group(2).split('\t')[0].strip()
            if jp in ('空', '陸', '海', '宇'):
                out.append(dict(category='ui', series='', jp=jp, en_source=en, source='gamefaqs:Move List', notes=''))
                continue
            if jp in sect:
                section = sect[jp]
            if ln.startswith(('\t', ' ')) or jp not in sect:
                if en:
                    out.append(dict(category=section if ln.startswith('\t') else 'ui', series='', jp=jp,
                                    en_source=re.sub(r'\s*\(.*', '', en), source='gamefaqs:Move List', notes=en))
                else:
                    pending = jp
    return out


def pilot_bin_names():
    """Nombres de PILOT.BIN: (completos, cortos). Los cortos solo cuentan para las decisiones (apodos del protagonista)."""
    path = os.path.join(WORK, 'iso_jp', 'UNITPRAM', 'PILOT.BIN')
    full, short = set(), set()
    if not os.path.exists(path):
        # sin la ISO (sesión en la nube): los mismos campos desde el volcado de pilot_bin.py
        for l in open(os.path.join(WORK, 'dump', 'pilot.jsonl'), encoding='utf-8'):
            d = json.loads(l)
            full.add(norm(d['full']))
            short.add(norm(d['short']))
        return full, short - {''}
    d = open(path, 'rb').read()
    n = int.from_bytes(d[:2], 'little')
    for i in range(n):
        base = 4 + i * 0x70
        full.add(norm(d[base + 4:base + 0x28].split(b'\0')[0].decode('cp932', 'replace')))
        short.add(norm(d[base + 0x29:base + 0x29 + 12].split(b'\0')[0].decode('cp932', 'replace')))
    return full, short - {''}


def main():
    if not os.path.isdir(TXT) or '--html' in sys.argv:
        html_to_txt()
    if not os.path.exists(os.path.join(OUT, 'web', 'official_terms.json')) or '--web' in sys.argv:
        fetch_official()
    rows = []
    rows += series_tables('Character List', 'pilot')
    rows += series_tables('Unit List', 'unit')
    rows += simple_table('Spirit', 'spirit', 0, 1)
    rows += simple_table('Pilot Ability', 'pilot_skill', 1, 0)
    rows += simple_table('Unit Ability', 'unit_ability', 1, 0)
    rows += simple_table('OP Parts', 'part', 1, 0)
    rows += move_list_terms()
    # glossary/manual.csv: términos que ninguna fuente trae (propuesta propia, status = proposed)
    manual = os.path.join(OUT, 'manual.csv')
    manual_final = {}
    if os.path.exists(manual):
        for m in csv.DictReader(open(manual, encoding='utf-8')):
            rows.append(dict(category=m['category'], series=m['series'], jp=m['jp'], en_source='',
                             source='manual', notes=m['notes']))
            manual_final[(m['category'], m['jp'])] = m['en_final']

    # armas: nombres reales del juego, de dump/robot.jsonl (robot_raf.py --json dump/robot.jsonl)
    robot = os.path.join(WORK, 'dump', 'robot.jsonl')
    if os.path.exists(robot):
        weapons = {}
        for line in open(robot, encoding='utf-8'):
            u = json.loads(line)
            for w in u['weapons']:
                n = norm(w['name'])
                if n and n != 'ダミー':
                    weapons.setdefault(n, []).append(norm(u['name']))
        for n, units in weapons.items():
            uniq_units = list(dict.fromkeys(units))
            rows.append(dict(category='weapon', series='', jp=n, en_source='', source='game:ROBOT.RAF',
                             notes=f"{len(uniq_units)} unidad(es): " + ', '.join(uniq_units[:4])
                             + (' …' if len(uniq_units) > 4 else '')))

    # unidades del juego sin entrada en la wiki (units_en.csv, 486 unidades de ROBOT.RAF)
    upath = os.path.join(OUT, 'units_en.csv')
    units_en = {}
    if os.path.exists(upath):
        for d in csv.DictReader(open(upath, encoding='utf-8')):
            st = {'official': 'official', 'fan-standard': 'source'}.get(d['status'], 'proposed')
            units_en[norm(d['jp_norm'])] = (d['en'], st, d.get('en_short', ''))
        known = {norm(r['jp']) for r in rows if r['category'] == 'unit'}
        for j in units_en:
            if j not in known:
                rows.append(dict(category='unit', series='', jp=j, en_source='', source='game:ROBOT.RAF', notes=''))

    # deduplicar por (categoría, jp): gana la primera fuente (Akurasu antes que GameFAQs)
    seen, uniq = {}, []
    for r in rows:
        k = (r['category'], norm(r['jp']))
        if k in seen:
            other = seen[k]
            if r['en_source'].lower() != other['en_source'].lower() and r['en_source'] not in other['notes']:
                alt = r['en_source'].split('\t')[0]
                other['notes'] = (other['notes'] + f"; alt {r['source']}: {alt}").strip('; ')
            continue
        seen[k] = r
        uniq.append(r)

    official = {}
    op = os.path.join(OUT, 'web', 'official_terms.json')
    if os.path.exists(op):
        official = {norm(k): v for k, v in json.load(open(op, encoding='utf-8')).items()}

    def best_official(jp):
        cands = official.get(norm(ALIASES.get(jp, jp))) or {}
        def rank(src):  # 'spirit_OGs', 'ogs_Parts', 'T_Parts' → posición de la entrega en OFFICIAL_ORDER
            game = src.removeprefix('spirit_').split('_')[0]
            game = 'ogs' if game.lower() == 'ogs' else game
            return OFFICIAL_ORDER.index(game) if game in OFFICIAL_ORDER else 99
        return sorted((min(rank(x) for x in srcs), en, srcs) for en, srcs in cands.items())

    pnames, pshort = pilot_bin_names()
    msgs = [norm(json.loads(l)['jp']) for l in open(os.path.join(WORK, 'dump', 'snmsg.jsonl'), encoding='utf-8')]
    blob = '\n'.join(msgs)

    # glossary/decisiones.csv: decisiones del responsable (status = manual; nunca se pisan)
    decisions, dshort = {}, {}
    dpath = os.path.join(OUT, 'decisiones.csv')
    if os.path.exists(dpath):
        for d in csv.DictReader(open(dpath, encoding='utf-8')):
            decisions[(d['category'], d['jp'])] = d['en_final']
            if d.get('en_short'):  # forma corta decidida (campos de largo fijo: PILOT.BIN ≤ 20, ROBOT.RAF ≤ 21)
                dshort[(d['category'], d['jp'])] = d['en_short']
    # glossary/proposed_review.csv: revisión de términos propuestos (recomendación; sigue como 'proposed')
    review = {}
    rpath = os.path.join(OUT, 'proposed_review.csv')
    if os.path.exists(rpath):
        for d in csv.DictReader(open(rpath, encoding='utf-8')):
            if d.get('recommended_en'):
                review[(d['category'], d['jp'])] = d['recommended_en']

    # glossary/weapons_en.csv (686 armas) y weapons_review.csv (revisión posterior: tiene prioridad)
    weapons_en = {}
    for fname in ('weapons_en.csv', 'weapons_review.csv'):
        wpath = os.path.join(OUT, fname)
        if os.path.exists(wpath):
            for d in csv.DictReader(open(wpath, encoding='utf-8')):
                st = {'official': 'official', 'fan-standard': 'source', 'proposed': 'proposed'}.get(d['status'], 'reviewed')
                weapons_en[norm(d['jp'])] = (d['en'], st, d.get('en_short', ''))

    # conservar ediciones manuales previas
    prev = {}
    path = os.path.join(OUT, 'glossary.csv')
    if os.path.exists(path):
        for r in csv.DictReader(open(path, encoding='utf-8')):
            prev[(r['category'], norm(r['jp']))] = r

    for r in uniq:
        j = norm(r['jp'])
        # nombre corto de PILOT.BIN: solo para decisiones sin alias al nombre completo (apodos del protagonista)
        r['in_pilot_bin'] = 'yes' if r['category'] == 'pilot' and (j in pnames or (
            (r['category'], r['jp']) in decisions and j in pshort and r['jp'] not in PILOT_GAME_ALIASES)) else ''
        r['jp_game'] = ''
        r.setdefault('en_short', '')
        if r['category'] == 'pilot' and not r['in_pilot_bin']:
            # grafía distinta en el juego (ーの位置, nombre corto, etc.): la más parecida de PILOT.BIN
            import difflib
            m = [PILOT_GAME_ALIASES[r['jp']]] if r['jp'] in PILOT_GAME_ALIASES else []
            m = m or difflib.get_close_matches(j, pnames, n=1, cutoff=0.6)
            m = m or [n for n in pnames if len(n) > 1 and (n in j or j in n)][:1]
            if m:
                r['jp_game'], r['in_pilot_bin'] = m[0], 'similar'
        r['snmsg_hits'] = blob.count(re.sub(r'\(.*?\)', '', j)) if len(j) > 1 else ''
        p = prev.get((r['category'], j))
        off = best_official(r['jp']) if r['category'] != 'pilot' and r['category'] != 'unit' else []
        r['en_official'] = '; '.join(f"{en} [{','.join(srcs)}]" for _, en, srcs in off)
        if (r['category'], r['jp']) in decisions:
            r['en_final'], r['status'] = decisions[(r['category'], r['jp'])], 'manual'
            if (r['category'], r['jp']) in dshort:
                r['en_short'] = dshort[(r['category'], r['jp'])]
            elif r['category'] == 'unit' and j in units_en:
                r['en_short'] = units_en[j][2]
        elif p and p.get('status') == 'manual':
            r['en_final'], r['status'] = p['en_final'], 'manual'
        elif off:
            r['en_final'], r['status'] = off[0][1], 'official'
        elif (r['category'], r['jp']) in review and r['category'] != 'weapon' and not off:
            r['en_final'], r['status'] = review[(r['category'], r['jp'])], 'proposed'
        elif (r['category'], r['jp']) in manual_final:
            r['en_final'], r['status'] = manual_final[(r['category'], r['jp'])], 'proposed'
        elif (r['category'], r['jp']) in PROPOSED:
            r['en_final'], r['status'] = PROPOSED[(r['category'], r['jp'])], 'proposed'
        elif r['category'] == 'weapon' and j in weapons_en:
            r['en_final'], r['status'], r['en_short'] = weapons_en[j]
        elif r['category'] == 'unit' and j in units_en:
            r['en_final'], r['status'], r['en_short'] = units_en[j]
        elif r['category'] == 'weapon':
            r['en_final'], r['status'] = '', 'pending'
        else:
            r['en_final'], r['status'] = r['en_source'], 'source'
        if p and p['notes'] != r['notes']:
            r['notes'] = p['notes']

    os.makedirs(OUT, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(uniq)
    from collections import Counter
    print(len(uniq), 'términos →', path)
    for k, v in Counter(r['category'] for r in uniq).most_common():
        print(f'  {k:13} {v}')
    miss = sorted(pnames - {norm(r['jp']) for r in uniq if r['category'] == 'pilot'}
                  - {r['jp_game'] for r in uniq if r['jp_game']})
    print(len(miss), 'nombres de PILOT.BIN sin entrada en el glosario')
    open(os.path.join(OUT, 'pilot_bin_missing.txt'), 'w').write('\n'.join(miss) + '\n')


if __name__ == '__main__':
    main()
