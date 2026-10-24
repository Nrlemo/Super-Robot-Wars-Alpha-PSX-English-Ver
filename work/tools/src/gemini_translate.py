#!/usr/bin/env python3
"""Traduce un lote (.jsonl de lote.py) con la API de Gemini, valida con check_text y repara lo que falle.
Solo librería estándar. Uso:
  gemini_translate.py LOTE.jsonl [--model M] [--chunk 40] [--repair 2] [--sleep 1] [--limit N] [--dry-run] [--mock]
Variables: GEMINI_API_KEY (obligatoria salvo --dry-run/--mock), GEMINI_MODEL (por defecto gemini-3.1-pro-preview),
TARGET_LANG (idioma de salida, por defecto English; ver docs/TRANSLATION_GUIDE.md).
Reanuda: las filas con `en` no se tocan. Guarda el lote después de cada tanda; escribe LOTE.informe.md."""
import argparse, csv, json, os, re, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lote as L  # noqa: E402

ROOT = L.ROOT
REF = ROOT / 'traduccion' / 'referencia'
API = os.environ.get('GEMINI_API_URL') or 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
# idioma de salida (un fork que traduce a otro idioma lo cambia; el prompt de PROMPT_API.md también)
TARGET_LANG = os.environ.get('TARGET_LANG') or 'English'
SCHEMA = {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {
    'k': {'type': 'INTEGER'}, 'en': {'type': 'STRING'}, 'notas': {'type': 'STRING'}}, 'required': ['k', 'en']}}
USAGE = {'in': 0, 'out': 0, 'calls': 0}


def leer(p):
    return Path(p).read_text(encoding='utf-8')


def guia_secciones(labels: set[str]) -> str:
    g = leer(ROOT / 'work' / 'notes' / 'guia_estilo_personajes.md')
    i, j = g.index('## 1. '), g.index('## 4. ')
    base = g[i:j]
    k = g.index('## 5. ')
    subs = re.split(r'(?m)^(?=### 4\.)', g[j:k])[1:]
    keys = {x for lab in labels for x in ([lab] + ([lab.split()[0]] if len(lab.split()[0]) >= 4 else []))
            if lab and not lab.startswith('$')}
    sel = [s for s in subs if any(x in s for x in keys)]
    return base + '\n' + ''.join(sel)


def ref_filtrada(jp_text: str) -> str:
    out = []
    for name in ('terminologia', 'lugares', 'facciones', 'naves'):
        rows = list(csv.DictReader(open(REF / f'{name}.csv', encoding='utf-8')))
        keep = [r for r in rows if r['jp'] and r['jp'] in jp_text]
        if keep:
            out.append(f'### {name}.csv (jp | en | tipo | notas)\n' + '\n'.join(
                f"{r['jp']} | {r['en']} | {r['tipo']} | {r['notas']}" for r in keep))
    fr = list(csv.DictReader(open(REF / 'frases_fijas.csv', encoding='utf-8')))
    keep = [r for r in fr if r['jp'] and r['jp'] in jp_text]
    if keep:
        out.append('### frases_fijas.csv (jp | en | tipo)\n' + '\n'.join(f"{r['jp']} | {r['en']} | {r['tipo']}" for r in keep))
    return '\n\n'.join(out)


def system_prompt(path: Path, rows: list[dict]) -> str:
    cast = Path(str(path) + '.reparto.tsv')
    terms = Path(str(path) + '.terminos.tsv')
    labels = {r['ctx']['hablante'] for r in rows if r.get('ctx', {}).get('hablante')}
    jp_text = '\n'.join(L.tref.flat(r['jp']) if hasattr(L.tref, 'flat') else r['jp'] for r in rows)
    parts = [leer(ROOT / 'traduccion' / 'PROMPT_API.md'),
             f'# REFERENCE — style guide (Spanish; output stays {TARGET_LANG})\n' + guia_secciones(labels),
             '# REFERENCE — the protagonist (8 variants)\n' + leer(REF / 'protagonistas.md')]
    if cast.exists():
        parts.append('# THIS BATCH — cast (personality, English voice, JP speech profile)\n' + leer(cast))
    if terms.exists():
        parts.append('# THIS BATCH — glossary terms to use EXACTLY (jp, en, en_corto...)\n' + leer(terms))
    rf = ref_filtrada(jp_text)
    if rf:
        parts.append('# THIS BATCH — places, factions, ships, terminology, iconic phrases\n' + rf)
    return '\n\n'.join(parts)


def pack(i: int, r: dict) -> dict:
    c = r.get('ctx', {})
    o = {'k': i, 'jp': r['jp']}
    for f in ('hablante', 'variante', 'quien', 'tipo', 'mision'):
        if c.get(f):
            o[f] = c[f]
    if r.get('tm'):
        o['tm'] = r['tm']
    if r.get('ref'):                            # inglés de referencia (fork que traduce desde el inglés)
        o['ref'] = r['ref']
    return o


def chunks(rows: list[dict], todo: list[int], size: int) -> list[list[int]]:
    out, cur = [], []
    for n, i in enumerate(todo):
        v = rows[i].get('ctx', {}).get('variante')
        cut = len(cur) >= size and not (v and v > 1)   # no partir un bloque de variantes 1..8
        if cur and (cut or len(cur) >= size + 8):
            out.append(cur); cur = []
        cur.append(i)
    if cur:
        out.append(cur)
    return out


class ApiDown(Exception):
    pass


_CACHE: dict = {}


def cache_for(model: str, system: str, key: str):
    """Context caching explícito del system prompt (1 h); si la API lo rechaza (prompt corto, modelo sin soporte) se sigue sin caché."""
    if os.environ.get('GEMINI_NO_CACHE') or os.environ.get('GEMINI_API_URL'):
        return None
    k = (model, hash(system))
    if k not in _CACHE:
        _CACHE[k] = None
        body = {'model': f'models/{model}', 'ttl': '3600s',
                'systemInstruction': {'parts': [{'text': system}]},
                'contents': [{'role': 'user', 'parts': [{'text': 'Reglas y glosario cargados.'}]}]}
        req = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/cachedContents',
                                     json.dumps(body).encode(), {'Content-Type': 'application/json', 'x-goog-api-key': key})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                _CACHE[k] = json.load(r)['name']
            print(f'  caché de contexto: {_CACHE[k]}', file=sys.stderr)
        except Exception as e:
            print(f'  sin caché de contexto ({str(e)[:80]})', file=sys.stderr)
    return _CACHE[k]


BACKEND = os.environ.get('TRAD_BACKEND') or 'gemini'   # gemini | anthropic (ANTHROPIC_API_KEY) | claude-cli (CLAUDE_CODE_OAUTH_TOKEN)
TOOL = {'name': 'traducciones', 'description': 'Devuelve las filas traducidas.', 'input_schema': {
    'type': 'object', 'required': ['filas'], 'properties': {'filas': {'type': 'array', 'items': {
        'type': 'object', 'required': ['k', 'en'],
        'properties': {'k': {'type': 'integer'}, 'en': {'type': 'string'}, 'notas': {'type': 'string'}}}}}}}


def parse_filas(text: str):
    a, b = text.find('['), text.rfind(']')
    try:
        return json.loads(text[a:b + 1]) if a >= 0 and b > a else []
    except json.JSONDecodeError:
        return []


def call_anthropic(model: str, system: str, user: str):
    key = os.environ.get('ANTHROPIC_API_KEY') or sys.exit('falta ANTHROPIC_API_KEY')
    body = {'model': model, 'max_tokens': 16000,
            'system': [{'type': 'text', 'text': system, 'cache_control': {'type': 'ephemeral'}}],
            'messages': [{'role': 'user', 'content': user}],
            'tools': [TOOL], 'tool_choice': {'type': 'tool', 'name': 'traducciones'}}
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode(),
                                 {'Content-Type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01'})
    wait = 5
    for attempt in range(9):
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                d = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:300]
            if e.code in (429, 500, 502, 503, 504, 529) and attempt < 8:
                print(f'  HTTP {e.code}, reintento en {wait}s', file=sys.stderr)
                time.sleep(wait); wait = min(wait * 2, 300); continue
            raise ApiDown(f'Anthropic HTTP {e.code}: {msg}')
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 8:
                time.sleep(wait); wait = min(wait * 2, 300); continue
            raise ApiDown(f'Anthropic: {e}')
    u = d.get('usage', {})
    USAGE['in'] += u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)
    USAGE['out'] += u.get('output_tokens', 0); USAGE['calls'] += 1
    for blk in d.get('content', []):
        if blk.get('type') == 'tool_use':
            return blk['input'].get('filas', []), d.get('stop_reason', '?')
    return [], d.get('stop_reason', '?')


def call_claude_cli(model: str, system: str, user: str):
    """Claude Code en modo headless con el login de la suscripción (CLAUDE_CODE_OAUTH_TOKEN = `claude setup-token`)."""
    cmd = ['claude', '-p', user + '\n\nReply with ONLY the JSON array, no prose, no code fences.', '--model', model,
           '--system-prompt', system, '--output-format', 'json', '--max-turns', '1']
    for attempt in range(4):
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        try:
            d = json.loads(p.stdout)
        except json.JSONDecodeError:
            d = {'is_error': True, 'result': (p.stdout + p.stderr)[:300]}
        if not d.get('is_error'):
            break
        txt = str(d.get('result', ''))
        if re.search(r'limit|quota|usage', txt, re.I) and not re.search(r'try again in \d+ ?s', txt, re.I):
            raise ApiDown(f'Claude: {txt[:200]}')
        if attempt == 3:
            raise ApiDown(f'Claude: {txt[:200]}')
        time.sleep(30 * (attempt + 1))
    u = d.get('usage', {})
    USAGE['in'] += u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)
    USAGE['out'] += u.get('output_tokens', 0); USAGE['calls'] += 1
    return parse_filas(str(d.get('result', ''))), d.get('subtype', 'success')


def call(model: str, system: str, user: str, mock: bool, rows_in: list[dict]) -> tuple[list[dict], str]:
    if mock:
        return [{'k': r['k'], 'en': (r['hablante'] + ': ' if r.get('hablante') else '') + f"Mock line {r['k']}."}
                for r in rows_in], 'STOP'
    if BACKEND == 'anthropic':
        return call_anthropic(model, system, user)
    if BACKEND == 'claude-cli':
        return call_claude_cli(model, system, user)
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        sys.exit('falta GEMINI_API_KEY')
    cache = cache_for(model, system, key)
    body = {'contents': [{'role': 'user', 'parts': [{'text': user}]}],
            'generationConfig': {'temperature': 0.5, 'maxOutputTokens': 32768, 'responseMimeType': 'application/json',
                                 'responseSchema': SCHEMA}}
    if cache:
        body['cachedContent'] = cache
    else:
        body['systemInstruction'] = {'parts': [{'text': system}]}
    req = urllib.request.Request(API.format(model=model), json.dumps(body).encode(),
                                 {'Content-Type': 'application/json', 'x-goog-api-key': key})
    wait = 5
    for attempt in range(9):
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                d = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            full = e.read().decode(errors='replace'); msg = full[:300]
            if e.code == 429 and re.search(r'PerDay|per day', full):
                raise ApiDown(f'Gemini HTTP 429 (cupo diario o saldo): {msg}')
            if e.code in (429, 500, 502, 503, 504) and attempt < 8:
                print(f'  HTTP {e.code}, reintento en {wait}s', file=sys.stderr)
                time.sleep(wait); wait = min(wait * 2, 300); continue
            raise ApiDown(f'Gemini HTTP {e.code}: {msg}')
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 8:
                time.sleep(wait); wait = min(wait * 2, 300); continue
            raise ApiDown(f'Gemini: {e}')
    u = d.get('usageMetadata', {})
    USAGE['in'] += u.get('promptTokenCount', 0); USAGE['out'] += u.get('candidatesTokenCount', 0) + u.get('thoughtsTokenCount', 0)
    USAGE['calls'] += 1
    cand = (d.get('candidates') or [{}])[0]
    reason = cand.get('finishReason', '?')
    text = ''.join(p.get('text', '') for p in cand.get('content', {}).get('parts', []))
    try:
        return json.loads(text), reason
    except json.JSONDecodeError:
        return [], reason


def ask(model, system, rows, idx, ctx_prev, mock, extra=''):
    """Traduce las filas idx; devuelve {i: (en, notas)}. Parte la tanda en dos si la respuesta vino incompleta."""
    pack_rows = [pack(n, rows[i]) for n, i in enumerate(idx)]
    user = ''
    if ctx_prev:
        user += 'Previous lines already translated (context only, do NOT return them):\n' + '\n'.join(ctx_prev) + '\n\n'
    user += extra + 'Translate these rows. Return a JSON array of {"k","en","notas"} for EVERY k:\n' + \
        json.dumps(pack_rows, ensure_ascii=False)
    res, reason = call(model, system, user, mock, pack_rows)
    got = {x['k']: x for x in res if isinstance(x, dict) and isinstance(x.get('k'), int) and x.get('en')}
    if len(got) == len(idx):
        return {idx[k]: (got[k]['en'], got[k].get('notas', '')) for k in got if 0 <= k < len(idx)}
    if len(idx) > 4:
        h = len(idx) // 2
        print(f'  respuesta incompleta ({len(got)}/{len(idx)}, {reason}): parto la tanda', file=sys.stderr)
        a = ask(model, system, rows, idx[:h], ctx_prev, mock, extra)
        b = ask(model, system, rows, idx[h:], ctx_prev, mock, extra)
        return {**a, **b}
    return {idx[k]: (got[k]['en'], got[k].get('notas', '')) for k in got if 0 <= k < len(idx)}


def problemas(path: Path, rows: list[dict], idx: list[int]) -> dict[int, list[str]]:
    """Errores (y avisos de hablante) de check_text para las filas idx, escribiendo un lote temporal."""
    tmp = path.with_suffix('.tmp.jsonl')
    L.write_jsonl(tmp, [rows[i] for i in idx])
    try:
        viol, _ = L.validate(tmp)
    finally:
        tmp.unlink(missing_ok=True)
    fmt = L.fmt_of(path)
    by_id = {'/'.join(str(rows[i][k]) for k in L.KEYS[fmt]): i for i in idx}
    out: dict[int, list[str]] = {}
    for v in viol:
        if v['severity'] == 'error' or v['kind'] == 'hablante':
            out.setdefault(by_id[v['id']], []).append(f"{v['kind']}: {v.get('value', '')} (limit {v.get('limit', '')}) {v.get('detail', '')}")
    return out


def main():
    global BACKEND
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('lote')
    ap.add_argument('--model', default=os.environ.get('GEMINI_MODEL') or 'gemini-3.1-pro-preview')
    ap.add_argument('--backend', choices=['gemini', 'anthropic', 'claude-cli'], default=BACKEND)
    ap.add_argument('--chunk', type=int, default=40)
    ap.add_argument('--repair', type=int, default=2)
    ap.add_argument('--sleep', type=float, default=1.0)
    ap.add_argument('--limit', type=int, default=0, help='traducir como mucho N filas (pruebas)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--mock', action='store_true')
    a = ap.parse_args()
    BACKEND = a.backend
    if BACKEND != 'gemini' and a.model.startswith('gemini'):
        a.model = os.environ.get('CLAUDE_MODEL') or 'claude-sonnet-5'
    path = Path(a.lote)
    rows = L.read_jsonl(path)
    todo = [i for i, r in enumerate(rows) if not r.get('en')]
    if a.limit:
        todo = todo[:a.limit]
    system = system_prompt(path, rows)
    tandas = chunks(rows, todo, a.chunk)
    print(f'{path.name}: {len(rows)} filas, {len(todo)} por traducir, {len(tandas)} tandas · prompt de sistema '
          f'{len(system):,} caracteres · modelo {a.model}')
    if a.dry_run or not todo:
        return 0
    notas, sin_resolver, corte = [], [], ''
    for n, idx in enumerate(tandas, 1):
        first = idx[0]
        prev = [f"{rows[i]['jp'].splitlines()[0][:60]} => {rows[i]['en'].splitlines()[0][:80]}"
                for i in range(max(0, first - 6), first) if rows[i].get('en')]
        try:
            res = ask(a.model, system, rows, idx, prev, a.mock)
        except ApiDown as e:
            corte = str(e)[:200]
            print(f'  API caída tras reintentos, se guarda lo hecho: {corte}', file=sys.stderr)
            break
        for i, (en, nt) in res.items():
            rows[i]['en'] = en
            if nt:
                rows[i]['notas'] = nt
        for ronda in range(a.repair):
            bad = problemas(path, rows, idx)
            if not bad:
                break
            bl = sorted(bad)
            extra = 'Some earlier translations FAILED the validator. Fix ONLY these rows (shorten/re-flow, keep names). Problems per k:\n' + \
                json.dumps({str(idx.index(i)): bad[i] for i in bl}, ensure_ascii=False) + '\nPrevious attempt per k:\n' + \
                json.dumps({str(idx.index(i)): rows[i]['en'] for i in bl}, ensure_ascii=False) + '\n\n'
            try:
                fix = ask(a.model, system, rows, bl, prev, a.mock, extra)
            except ApiDown as e:
                corte = str(e)[:200]
                break
            for i, (en, nt) in fix.items():
                rows[i]['en'] = en
                if nt:
                    rows[i]['notas'] = nt
            time.sleep(a.sleep)
        for i, msgs in problemas(path, rows, idx).items():
            sin_resolver.append((rows[i], msgs))
        L.write_jsonl(path, rows)
        print(f'  tanda {n}/{len(tandas)} ok · llamadas {USAGE["calls"]} · tokens in/out {USAGE["in"]:,}/{USAGE["out"]:,}', flush=True)
        time.sleep(a.sleep)
    viol, n_err = L.validate(path)
    rep = Path(str(path).removesuffix('.jsonl') + '.informe.md')
    fmt = L.fmt_of(path)
    lines = [f'# Informe de traducción: {path.name}', '',
             f'- Modelo: `{a.model}`{" (MOCK)" if a.mock else ""} · llamadas: {USAGE["calls"]} · tokens in/out: {USAGE["in"]:,}/{USAGE["out"]:,}',
             f'- Filas: {sum(1 for r in rows if r.get("en"))}/{len(rows)} con inglés · errores del validador: **{n_err}** · avisos: {len(viol) - n_err}', '']
    if corte:
        lines += [f'> **Corrida cortada por la API** ({corte}). Faltan {sum(1 for r in rows if not r.get("en"))} filas: '
                  'volver a lanzar el mismo lote retoma donde quedó.', '']
    dud = [r for r in rows if r.get('notas')]
    if dud:
        lines += ['## Notas del traductor (juegos de palabras, DUDOSO)', ''] + [
            f"- `{'/'.join(str(r[k]) for k in L.KEYS[fmt])}` {r['jp'].splitlines()[0][:40]} → {r['notas']}" for r in dud] + ['']
    if n_err:
        lines += ['## Errores sin resolver', ''] + [
            f"- `{v['id']}` {v['kind']}: {v.get('value', '')} (tope {v.get('limit', '')}) {v.get('detail', '')}" for v in viol if v['severity'] == 'error'] + ['']
    warn = [v for v in viol if v['severity'] != 'error']
    if warn:
        lines += ['## Avisos', ''] + [f"- `{v['id']}` {v['kind']}: {v.get('value', '')} → {v.get('limit', '')}" for v in warn[:80]]
    rep.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'informe → {rep} · errores {n_err}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
