"""Lotes de traducción: sacar del volcado con contexto, listar términos, validar e integrar el `en` en work/dump/.

Uso (desde la raíz del repo; solo stdlib, no necesita la ISO):
  python3 work/tools/src/lote.py sacar script 1-3            # escenas 1 a 3 de SCRIPT.BIN
  python3 work/tools/src/lote.py sacar snmsg --bloque 1      # mensajes de mapa del bloque 1 de SNDATA (escenario 1, ruta super)
  python3 work/tools/src/lote.py sacar snmsg 47-120          # rango de slots de SNMSG
  python3 work/tools/src/lote.py sacar bxclist 0-9           # frases de batalla de los pilotos 0 a 9 (ID de PILOT.BIN)
  python3 work/tools/src/lote.py sacar deadmess 0-99 | sacar em 0-29
  python3 work/tools/src/lote.py terminos traduccion/lotes/script/script_001-003.jsonl
  python3 work/tools/src/lote.py validar  traduccion/lotes/script/script_001-003.jsonl
  python3 work/tools/src/lote.py integrar traduccion/lotes/script/script_001-003.jsonl [--forzar]
  python3 work/tools/src/lote.py estado                      # filas traducidas por formato (work/dump/)

Un lote es un JSONL con las claves del volcado (script/inst, id, pilot/idx, slot, rec) + `jp`, `en`, `ctx` (contexto:
hablante en inglés, variante 1–8 del protagonista, escenario, título, tipo de mensaje…) y `tm` (sugerencia: la misma
línea japonesa ya traducida en otro lado). En un fork que traduce a otro idioma desde el inglés (kit.py pivot) va
además `ref`: el inglés de referencia de esa fila (`en_ref` del volcado). Junto al lote queda `<lote>.terminos.tsv`: los términos del glosario
unificado (traduccion/referencia/generado/) que aparecen en su japonés, y `<lote>.reparto.tsv`: los personajes que
hablan en el lote con su personalidad y voz (traduccion/referencia/hablantes.csv). `validar` corre check_text.py sobre el lote
y además avisa si falta el prefijo del hablante o un término del glosario. `integrar` copia los `en` no vacíos al
volcado (verifica que el `jp` coincida) y se niega si `validar` da errores, salvo --forzar.
"""
import argparse, collections, csv, json, re, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_text  # noqa: E402
import reflow_candidates  # noqa: E402

REFLOW_FMTS = ('script', 'snmsg', 'em', 'deadmess', 'bxclist')
import traduccion_ref as tref  # noqa: E402

ROOT = tref.ROOT
DUMP = tref.DUMP
LOTES = ROOT / 'traduccion' / 'lotes'
LOGS = ROOT / 'work' / 'logs'
KEYS = {'snmsg': ('id',), 'script': ('script', 'inst'), 'bxclist': ('pilot', 'idx'), 'deadmess': ('slot',), 'em': ('rec',)}
RANGE_FIELD = {'snmsg': 'id', 'script': 'script', 'bxclist': 'pilot', 'deadmess': 'slot', 'em': 'rec'}
SPEAKER = tref.SPEAKER
# Variante k (1–8) = protagonista k; la pareja que habla en la variante k es la pareja del protagonista k (guía §3).
# La variante es género × personalidad (el jugador elige cara y personalidad; los nombres son los preajustes):
# ver traduccion/referencia/protagonistas.md.
PERSONALIDAD = ['serious & just', 'calm & brilliant', 'shy & kind', 'cheerful optimist']
PROTAS = [f'{n} ({g}, {p})' for n, g, p in zip(['Bullet', 'Yuuki', 'Ryoto', 'Tasuku', 'Rio', 'Leona', 'Kusuha', 'Carla'],
                                              ['male'] * 4 + ['female'] * 4, PERSONALIDAD * 2)]
PAREJA = [PROTAS[i] for i in (6, 7, 4, 5, 2, 3, 0, 1)]
# Tipos del glosario unificado que se controlan en `validar` (armas, sistema y rangos dan demasiado ruido)
CHECK_TIPOS = ('hablante', 'pilot', 'unit', 'lugares:', 'facciones:', 'naves:', 'terminologia:', 'mision')


def norm(s: str) -> str:
    """Igual que glossary_build.norm: NFKC, guiones/iguales de medio ancho → ー / ・, sin espacios."""
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(?<=[ァ-ヴー])-', 'ー', s).replace('=', '・').replace('＝', '・')
    return re.sub(r'\s+', '', s)


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    tmp.replace(path)


def fmt_of(path: Path) -> str:
    rows = read_jsonl(path)
    for fmt, keys in KEYS.items():
        if rows and all(k in rows[0] for k in keys) and (fmt != 'snmsg' or 'script' not in rows[0]):
            return fmt
    sys.exit(f'{path}: no se reconoce el formato del lote')


def key(fmt: str, r: dict) -> tuple:
    return tuple(r[k] for k in KEYS[fmt])


def parse_range(s: str) -> tuple[int, int]:
    a, _, b = s.partition('-')
    return int(a), int(b or a)


# ───────────────────────────── contexto ─────────────────────────────
def load_ctx_tables():
    _, hab = tref.read_csv(tref.REF / 'hablantes.csv')
    labels = {r['jp']: r['en'] for r in hab}
    g, _ = tref.glossary_corrected()
    pil = {}
    for r in g:
        if r['category'] == 'pilot':
            for j in (r['jp'], r.get('jp_game', '')):
                if j:
                    pil.setdefault(norm(j), r['en_final'])
    _, mis = tref.read_csv(tref.REF / 'misiones.csv')
    titles = {r['jp']: r['en'] for r in mis}
    return labels, pil, titles


def script_variants(rows: list[dict]) -> dict:
    """(script, inst) → variante 1–8 para las líneas de $n/$l que vienen en bloques de 8 consecutivos."""
    out, run = {}, []

    def flush():
        if run and len(run) % 8 == 0:
            for i, r in enumerate(run):
                out[(r['script'], r['inst'])] = i % 8 + 1
        run.clear()
    for r in rows:
        m = SPEAKER.match(r['jp'])
        s = m.group(1) if m else ''
        if s in ('$n', '$l') and (not run or (run[-1]['script'] == r['script'] and SPEAKER.match(run[-1]['jp']).group(1) == s)):
            run.append(r)
            continue
        flush()
        if s in ('$n', '$l'):
            run.append(r)
    flush()
    return out


def who(speaker: str, var: int | None) -> str:
    if not var:
        return ''
    return {'$n': PROTAS, '$l': PAREJA, '$N': PAREJA}.get(speaker, [''] * 8)[var - 1]


def tm_table() -> dict:
    """Memoria de traducción exacta: jp → en de todas las filas ya traducidas de los volcados."""
    tm = {}
    for fmt in KEYS:
        for r in read_jsonl(DUMP / f'{fmt}.jsonl'):
            if r.get('en'):
                tm.setdefault(r['jp'], r['en'])
    return tm


def cmd_sacar(a):
    fmt = a.formato
    rows = read_jsonl(DUMP / f'{fmt}.jsonl')
    labels, pil, titles = load_ctx_tables()
    smap = {}
    if fmt == 'snmsg':
        with open(DUMP / 'sndata_map.csv', encoding='utf-8') as f:
            smap = {int(r['slot']): r for r in csv.DictReader(f)}
    if a.bloque is not None:
        if fmt != 'snmsg':
            sys.exit('--bloque solo vale para snmsg')
        sel = [r for r in rows if smap.get(r['id'], {}).get('bloque') == str(a.bloque)]
        desc = f'bloque{a.bloque:03d}'
    elif a.rango:
        lo, hi = parse_range(a.rango)
        sel = [r for r in rows if lo <= r[RANGE_FIELD[fmt]] <= hi]
        desc = f'{lo:03d}-{hi:03d}' if lo != hi else f'{lo:03d}'
    else:
        sys.exit('falta el rango (p. ej. 1-3) o --bloque N')
    if not sel:
        sys.exit('el rango no tiene filas')
    variants = script_variants([r for r in rows if lo <= r['script'] <= hi]) if fmt == 'script' else {}
    tm = tm_table()
    out = []
    for r in sel:
        ctx = {}
        m = SPEAKER.match(r['jp'])
        spk = m.group(1) if m else (r.get('speaker') or '' if fmt == 'snmsg' else '')
        if spk:
            ctx['hablante'] = labels.get(spk, '?' + spk)
        if fmt == 'script':
            v = variants.get((r['script'], r['inst']))
            if v:
                ctx['variante'], ctx['quien'] = v, who(spk, v)
        elif fmt == 'snmsg':
            s = smap.get(r['id'], {})
            ctx.update({k: s[k] for k in ('bloque', 'escenario', 'ruta', 'tipo') if s.get(k)})
            if s.get('titulo_jp'):
                ctx['mision'] = titles.get(s['titulo_jp'], s['titulo_jp'])
            if s.get('variante'):
                ctx['variante'] = int(s['variante'])
                ctx['quien'] = who('$n' if s['tipo'] == 'protagonista' else '$N', ctx['variante'])
            if r.get('chs'):
                ctx['chs'] = r['chs']
        else:
            name = r.get('speaker_name') or r.get('pilot_name') or r.get('name', '')
            if name:
                n = norm(name)
                # PILOT.BIN corta los nombres largos a 20 bytes: si no hay coincidencia exacta, probar por prefijo
                ctx['piloto'] = pil.get(n) or next((en for j, en in pil.items() if len(n) >= 4 and j.startswith(n)), name)
            for k in ('tipo', 'grupo', 'variant', 'type'):
                if k in r:
                    ctx[k] = r[k]
        o = {k: r[k] for k in KEYS[fmt]}
        o.update({'jp': r['jp'], 'en': r.get('en', ''), 'ctx': ctx})
        if r.get('en_ref'):                     # fork desde el inglés (kit.py pivot): el inglés es la fuente principal
            o['ref'] = r['en_ref']
        if not r.get('en') and r['jp'] in tm:
            o['tm'] = tm[r['jp']]
        out.append(o)
    path = Path(a.salida) if a.salida else LOTES / fmt / f'{fmt}_{desc}.jsonl'
    if path.exists() and a.reusar:
        print(f'LOTE={path.relative_to(ROOT)}')
        return
    if path.exists() and not a.forzar:
        sys.exit(f'{path} ya existe (puede tener trabajo): usar --forzar para pisarlo')
    write_jsonl(path, out)
    n_terms = write_terms(path, out)
    n_cast = write_cast(path, out)
    print(f'LOTE={path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}')
    print(f'{path}: {len(out)} filas ({sum(1 for o in out if o["en"])} ya traducidas, '
          f'{sum(1 for o in out if "tm" in o)} con sugerencia tm) · {n_terms} términos · {n_cast} personajes '
          f'→ {path.name}.terminos.tsv / .reparto.tsv')


# ───────────────────────────── términos ─────────────────────────────
def load_unified() -> list[dict]:
    path = tref.GEN / 'glosario_unificado.tsv'
    if not path.exists():
        sys.exit(f'falta {path}: correr work/tools/src/traduccion_ref.py')
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


KANA = re.compile(r'[ぁ-んァ-ヴー・＝]+')
KATA = re.compile(r'[ァ-ヴー・＝]+')


def terms_in(text: str, uni: list[dict]) -> list[dict]:
    """Términos presentes en el texto, más largos primero; un tramo ya reconocido no vuelve a contar.
    Ruido evitado: términos de solo kana necesitan ≥ 3 caracteres, y los de katakana no pueden estar pegados
    a otra katakana (ダー no matchea en リーダー; ゲッター no matchea dentro de ゲッターロボ)."""
    found, seen = [], set()
    for t in sorted(uni, key=lambda t: -len(t['jp'])):
        jp = t['jp']
        if jp in seen or len(jp) < 2 or (KANA.fullmatch(jp) and len(jp) < 3) or jp not in text:
            continue
        pat = re.escape(jp)
        if KATA.fullmatch(jp):
            pat = r'(?<![ァ-ヴー])' + pat + r'(?![ァ-ヴー])'
        if not re.search(pat, text):
            continue
        seen.add(jp)
        found.append(t)
        text = re.sub(pat, lambda m: '\0' * len(m.group(0)), text)
    return found


def write_terms(path: Path, rows: list[dict]) -> int:
    text = '\n'.join(tref.flat(r['jp']) for r in rows)
    found = terms_in(text, load_unified())
    with open(Path(str(path) + '.terminos.tsv'), 'w', encoding='utf-8') as f:
        f.write('jp\ten\ten_corto\ttipo\tarchivo\n')
        f.writelines(f"{t['jp']}\t{t['en']}\t{t['en_corto']}\t{t['tipo']}\t{t['archivo']}\n" for t in found)
    return len(found)


def write_cast(path: Path, rows: list[dict]) -> int:
    """<lote>.reparto.tsv: quién habla en el lote, con personalidad, voz inglesa y perfil de habla (hablantes.csv)."""
    _, hab = tref.read_csv(tref.REF / 'hablantes.csv')
    by_jp = {r['jp']: r for r in hab}
    by_full = {r['nombre_completo']: r for r in hab}
    n = collections.Counter()
    for r in rows:
        m = SPEAKER.match(r['jp'])
        h = by_jp.get(m.group(1)) if m else by_full.get(r.get('ctx', {}).get('piloto', ''))
        if h:
            n[h['jp']] += 1
    cols = ['jp', 'en', 'nombre_completo', 'lineas_lote', 'personalidad', 'voz_en', 'habla_jp', 'temperamento']
    with open(Path(str(path) + '.reparto.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(cols) + '\n')
        for jp, c in n.most_common():
            h = by_jp[jp]
            f.write('\t'.join([jp, h['en'], h['nombre_completo'], str(c)] + [h.get(k, '') for k in cols[4:]]) + '\n')
    return len(n)


def cmd_terminos(a):
    path = Path(a.lote)
    rows = read_jsonl(path)
    print(f'{write_terms(path, rows)} términos → {path}.terminos.tsv · {write_cast(path, rows)} personajes → {path}.reparto.tsv')


# ───────────────────────────── validar ─────────────────────────────
def validate(path: Path) -> tuple[list[dict], int]:
    fmt = fmt_of(path)
    f = check_text.FORMATS[fmt]
    rows = read_jsonl(path)
    labels, _, _ = load_ctx_tables()
    uni = [t for t in load_unified() if t['tipo'].startswith(CHECK_TIPOS) and not t['tipo'].endswith(':rango')]
    out = []
    for r in rows:
        en = r.get('en') or ''
        if not en:
            continue
        rid = '/'.join(str(r[k]) for k in KEYS[fmt])
        for v in check_text.check_text(en, r['jp'], f):
            out.append({'id': rid, **v})
        m = SPEAKER.match(r['jp'])
        if m and fmt in ('script', 'snmsg', 'em'):
            lab = labels.get(m.group(1), m.group(1))
            if not en.startswith(lab + ':'):
                out.append({'id': rid, 'kind': 'hablante', 'severity': 'warn', 'value': en.split(':')[0][:20],
                            'limit': lab + ':', 'detail': 'la línea debería empezar con "Etiqueta:" (formato A, guía §1.3)'})
        low = en.lower()
        for t in terms_in(tref.flat(r['jp']), uni):
            cands = {t['en'], t['en_corto']} - {''}
            if not any(c.lower().rstrip('s') in low for c in cands):
                out.append({'id': rid, 'kind': 'termino', 'severity': 'warn', 'value': t['jp'], 'limit': t['en'],
                            'detail': f"término de {t['archivo']} no encontrado en el inglés"})
    return out, sum(1 for v in out if v['severity'] == 'error')


def cmd_validar(a):
    path = Path(a.lote)
    viol, n_err = validate(path)
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f'validar_{path.stem}.csv'
    with open(log, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, ['id', 'kind', 'severity', 'line', 'value', 'limit', 'detail'], extrasaction='ignore')
        w.writeheader()
        w.writerows(viol)
    rows = read_jsonl(path)
    kinds = collections.Counter((v['kind'], v['severity']) for v in viol)
    det = ', '.join(f'{k}:{c}' + ('?' if s == 'warn' else '') for (k, s), c in sorted(kinds.items())) or 'sin problemas'
    print(f'{path.name}: {sum(1 for r in rows if r.get("en"))}/{len(rows)} traducidas · errores {n_err} · '
          f'avisos {len(viol) - n_err} · {det}')
    for v in viol[:15]:
        print(f"  {v['id']:>10} {v['severity']:5} {v['kind']:9} {v.get('value', '')} (tope {v.get('limit', '')}) {v.get('detail', '')}")
    if len(viol) > 15:
        print(f'  … {len(viol) - 15} más → {log}')
    return n_err


# ───────────────────────────── integrar / estado ─────────────────────────────
def cmd_integrar(a):
    path = Path(a.lote)
    fmt = fmt_of(path)
    if cmd_validar(a) and not a.forzar:
        sys.exit('hay errores: corregir el lote o usar --forzar')
    batch = {key(fmt, r): r for r in read_jsonl(path) if r.get('en')}
    dump_path = DUMP / f'{fmt}.jsonl'
    rows = read_jsonl(dump_path)
    names = check_text.pilot_short_names() if fmt == 'deadmess' else {}
    upd = same = bad = 0
    for r in rows:
        b = batch.pop(key(fmt, r), None)
        if not b:
            continue
        if b['jp'] != r['jp']:
            bad += 1
            continue
        if r.get('en') == b['en']:
            same += 1
            continue
        r['en'] = b['en']
        if fmt in REFLOW_FMTS:      # #266: une los saltos a mitad de frase heredados del japonés
            r['en'] = reflow_candidates.reflow_text(fmt, r, names) or r['en']
        upd += 1
    write_jsonl(dump_path, rows)
    print(f'{dump_path.name}: {upd} actualizadas, {same} iguales, {bad} con jp distinto (omitidas), {len(batch)} claves inexistentes')


def cmd_estado(a):
    print(f'{"formato":9} {"filas":>7} {"trad.":>7} {"%":>6}')
    for fmt in KEYS:
        rows = read_jsonl(DUMP / f'{fmt}.jsonl')
        n = sum(1 for r in rows if r.get('en'))
        print(f'{fmt:9} {len(rows):7} {n:7} {100 * n / len(rows):6.1f}')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sacar', help='crear un lote desde work/dump/')
    s.add_argument('formato', choices=list(KEYS))
    s.add_argument('rango', nargs='?', help='N o N-M (script: n.º de escena; snmsg: slot; bxclist: piloto; deadmess: slot; em: registro)')
    s.add_argument('--bloque', type=int, help='snmsg: todos los mensajes de un bloque de SNDATA (ver misiones.csv)')
    s.add_argument('--salida', help='ruta del lote (por defecto traduccion/lotes/<formato>/…)')
    s.add_argument('--forzar', action='store_true', help='pisar un lote existente')
    s.add_argument('--reusar', action='store_true', help='si el lote ya existe, no tocarlo (imprime LOTE=ruta)')
    s.set_defaults(fn=cmd_sacar)
    for name, fn, hlp in (('terminos', cmd_terminos, 'regenerar <lote>.terminos.tsv y <lote>.reparto.tsv'),
                          ('validar', cmd_validar, 'check_text + hablante + términos'),
                          ('integrar', cmd_integrar, 'copiar los en del lote al volcado')):
        p = sub.add_parser(name, help=hlp)
        p.add_argument('lote')
        if name == 'integrar':
            p.add_argument('--forzar', action='store_true', help='integrar aunque validar dé errores')
        p.set_defaults(fn=fn)
    sub.add_parser('estado', help='avance por formato').set_defaults(fn=cmd_estado)
    a = ap.parse_args(argv)
    return 1 if a.fn(a) else 0


if __name__ == '__main__':
    sys.exit(main())
