"""Validador único de las traducciones: mide el campo "en" de todos los volcados como lo haría el juego.

Uso (desde work/):
  check_text.py [--only snmsg,script,...] [--input FMT=ruta.jsonl ...] [--csv salida.csv]
  check_text.py --wrap propuestas.jsonl          # además propone saltos de línea para lo que no entra
  check_text.py --wrap-text "texto inglés" [--format snmsg]   # prueba rápida de un texto suelto
  python3 -m unittest test_check_text             # (desde tools/src) pruebas con líneas sintéticas

Para cada fila con "en" no vacío (o, si falta, "en_ref": el inglés de un fork que traduce a otro idioma):
  1. Codifica como el juego: cp932, espacio → 0xA0, "\\n" → 0x0A, escapes {XX} (sjis_text.encode).
  2. Mide cada línea en px con la tabla VWF (patches/vwf_table.bin; si no existe —es *.bin, no está en git— la
     calcula desde font/en_8px.txt con la misma regla que font_build.py).
  3. Controla bytes, líneas y px según el formato (tabla FORMATS abajo), variables $n/$N/... iguales a "jp",
     y que no haya ﾞ/ﾟ (0xDE/0xDF) sueltos detrás de un carácter (el maquetador los toma como marca de glifo especial).
Severidad: "error" = límite verificado (formato del archivo o medido en el juego); "warn" = límite supuesto (ver
`assumed` en cada formato). Sale con código 1 si hay errores.
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from sjis_text import encode

WORK = Path(__file__).resolve().parents[2]
VWF_TABLE = WORK / 'patches' / 'vwf_table.bin'
FONT_TXT = WORK / 'font' / 'en_8px.txt'


# ───────────────────────────── Límites por formato (editar acá) ─────────────────────────────
@dataclass
class Fmt:
    file: str
    max_bytes: int | None      # bytes del texto codificado, sin el NUL; None = sin tope fijo
    max_lines: int | None
    line_px: int | None        # ancho máximo de línea en px; None = desconocido (se mide igual, no se controla)
    kana_px: int = 12          # avance de hiragana/katakana SJIS (el diálogo de mapa usa 8)
    assumed: set = field(default_factory=set)   # límites NO verificados → severidad "warn"
    speaker: bool = False      # diálogo con el hablante dentro del texto: controla el formato `Nombre: texto`
    note: str = ''


FORMATS = {
    # Slot fijo de 256 bytes (formato). 240 px medidos en emulador (poc_snmsg.md); 3 líneas visibles.
    'snmsg': Fmt('snmsg.jsonl', 255, 3, 240, kana_px=8, speaker=True,
                 note='SNMAP/SNMSG.BIN: slot de 256 bytes, caja de 3×240 px'),
    # kana_px=8 en SCRIPT/BXCLIST/DEADMESS: con 12 px, 2.160 líneas japonesas de SCRIPT y 302 de BXCLIST pasarían
    # de 240 px; con 8 px quedan 14 y 0 → la caja probablemente sea la del mapa (ver notes/check_text.md).
    # Largo libre (script_bin.py recalcula tamaños). Medido en el juego (#31, `formato_test.sh ancho`): la caja de
    # escena parte sola por carácter al pasar 272 px (34 dígitos entran, 35 no) y descarta los renglones después del 3.º.
    'script': Fmt('script.jsonl', None, 3, 272, kana_px=8, speaker=True,
                  note='BUSTUP/SCRIPT.BIN: escenas; caja 3×272 px (medida)'),
    # Largo libre por frase (bxclist.py rehace punteros). Medido (#31, `ancho_test.sh bx`): 2 renglones (el 3.º se
    # dibuja debajo de la caja), parte sola al pasar 240 px y el juego agrega 「 al principio y 」 al final (12 px c/u).
    'bxclist': Fmt('bxclist.jsonl', None, 2, 240, kana_px=8,
                   note='BATTLE/BXCLIST.BIN: frases de combate; ventana 2×240 px (sin 「」: se quitaron en BTL_GRP)'),
    # Slot de 256 bytes = u32 tipo + 252 de texto con NUL (formato). Probado en juego (notes/deadmess_em.md): sale en
    # la ventana del mapa (3×240 px) como `nombre_corto「texto」` — el juego agrega nombre (PILOT.BIN +0x29) y 「」:
    # el renglón 1 pierde nombre + ": " (ver DEADMESS_PREFIX / iter_rows).
    'deadmess': Fmt('deadmess.jsonl', 251, 3, 240, kana_px=8,
                    note='SNMAP/DEADMESS.BIN: frases al ser derribado; caja del mapa 3×240 px con nombre delante'),
    # Registro de 264 bytes = 8 de cabecera + 256 de texto con NUL (formato). Probado en juego (notes/deadmess_em.md):
    # misma caja que el mapa (retrato + 3×240 px); el nombre va dentro del texto (el juego no agrega nada).
    'em': Fmt('em.jsonl', 255, 3, 240, kana_px=8,
              note='SNMAP/EM.BIN: mensajes al suspender; caja del mapa 3×240 px'),
    # Registro de 20 B = 4 de cabecera + campo de 16 B con NUL (mdata_bin.py, #221): el inglés ≤ 15 bytes, 1 renglón.
    # Ancho de la ventana de terreno/lugar sin medir en el juego (line_px None).
    'mdata': Fmt('mdata.jsonl', 15, 1, None, kana_px=8,
                 note='SNMAP/MDATA.BIN + TEST/MDATA.BIN: nombres de terreno y lugares; campo de 16 B'),
    # Campos de ancho fijo: topes de bytes del layout confirmado (option_dict.LAYOUT: cabecera = campo − 1, líneas de
    # la ficha y casilleros del índice 46). Medido en el juego (#15, tools/dict_test.sh): la caja de la biografía deja
    # ~270 px (46 letras ≈ 210 px); serie y seiyuu admiten 2 líneas (\n), como en el japonés.
    'dc': Fmt('dc.jsonl', None, 2, 264,
              note='OPTION/DC.BIN: diccionario de personajes; tope de bytes por campo según option_dict.LAYOUT'),
    'dr': Fmt('dr.jsonl', None, 2, 264,
              note='OPTION/DR.BIN: diccionario de robots; ídem'),
}

# Reserva por variable = peor caso con los topes del editor de nombres, 8/8/8 (notes/nombres_protagonistas.md §7):
# letra más ancha de la fuente VWF = 6 px. Apodo ≤ 8 → 48 px; nombre ≤ 8 → 48 px; apellido ≤ 9 (el editor corta
# en 8, pero el valor por defecto "Luckfield" tiene 9) → 54 px; nombre completo 8 + espacio + 9 → 108 px.
VAR_PX = {'n': 48, 'N': 48, 'l': 48,
          'm': 48, 'M': 48, 's': 54, 'S': 54,
          'f': 108, 'F': 108, 'L': 108}
NAME_VAR_PX = VAR_PX['n']
EN_SPACE = '{A0}'       # espacio del texto inglés (0x20 queda en 8 px para alinear menús; notes/fuente_en.md)
VAR = re.compile(r'\$[nNfFmMsSlL]')
# Decisión de mapa (SNMSG): «　X選択» + una opción 「…」 por línea; el motor toma cada línea como opción (#266).
CHOICE = re.compile(r'^\u3000?[^\n「」]*選択(\n「[^\n]*」)+$')


def is_choice(jp: str) -> bool:
    return bool(CHOICE.match(jp or ''))
# Formato de diálogo decidido en el emulador (#23, guia_estilo_personajes.md §1.3): `Nombre: texto`, pensamientos
# `Nombre: (texto)`, renglones 2–3 sin sangría. JP_SPEAKER reconoce el hablante japonés (`タシロ「`, `$n（`).
JP_SPEAKER = re.compile(r'^([^\s「（」）\n]{1,16})[「（]')
EN_SPEAKER = re.compile(r'^[^\s:「（\n][^:「（\n]{0,23}: \S')


def speaker_issues(en: str, jp: str) -> list[str]:
    """Problemas de formato `Nombre: texto` en una línea de diálogo cuyo japonés empieza con un hablante."""
    if not JP_SPEAKER.match(jp):
        return []
    out = []
    if not EN_SPEAKER.match(en):
        out.append('no empieza con "Nombre: "')
    if any(c in en for c in '「」（）'):
        out.append('lleva 「」/（） (usar "Nombre: texto" / "Nombre: (texto)")')
    if any(ln[:1] in (' ', '\u3000') for ln in en.split('\n')[1:]):
        out.append('renglón 2–3 con sangría')
    return out
MARKERS = (0xDE, 0xDF)  # ﾞ / ﾟ: detrás de un byte simple cambian el glifo (notes/pilot_bin.md)


# ───────────────────────────── Tabla de anchos ─────────────────────────────
def table_from_font(path: Path) -> bytes:
    """Misma regla que font_build.build: avance = ancho del dibujo + 1, adv=N lo fuerza, keep = 8, resto 8."""
    table = bytearray([8] * 256)
    cur, adv, width = None, None, None

    def close():
        if cur is not None and adv != 'keep':
            table[cur] = adv if adv is not None else (width or 0) + 1

    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('== '):
            close()
            parts = line[3:].split()
            name = parts[0]
            cur = 0x20 if name == 'space' else int(name, 16) if name.startswith('0x') else ord(name)
            adv = 'keep' if 'keep' in parts[1:] else next((int(p[4:]) for p in parts[1:] if p.startswith('adv=')), None)
            width = None
        elif cur is not None and line.strip() and width is None:
            width = len(line.strip())
    close()
    return bytes(table)


def load_table() -> tuple[bytes, str]:
    if VWF_TABLE.exists():
        return VWF_TABLE.read_bytes(), str(VWF_TABLE.relative_to(WORK))
    if FONT_TXT.exists():
        return table_from_font(FONT_TXT), f'{FONT_TXT.relative_to(WORK)} (vwf_table.bin no encontrada)'
    return bytes([8] * 256), 'ancho fijo de 8 px (sin tabla ni fuente)'


ADV, ADV_SRC = load_table()


# ───────────────────────────── Medición ─────────────────────────────
def to_game(text: str) -> str:
    return text.replace(' ', EN_SPACE)


def line_px(line: str, kana_px: int = 12, adv: bytes = None) -> int:
    """Ancho en px de una línea inglesa (sin \\n), como el maquetador FUN_80018CC4 con el parche VWF."""
    adv = adv or ADV
    px = sum(VAR_PX[v[1]] for v in VAR.findall(line))
    raw, i, prev = encode(to_game(VAR.sub('', line))), 0, None   # prev = último byte simple
    while i < len(raw):
        b = raw[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(raw):
            code = (b << 8) | raw[i + 1]
            px += kana_px if 0x829F <= code <= 0x82F1 or 0x8340 <= code <= 0x8396 else 12
            i, prev = i + 2, None
        else:
            # ﾞ/ﾟ detrás de un byte simple no avanzan: forman un solo glifo de 8 px con el anterior
            if b in MARKERS and prev is not None:
                px += 8 - adv[prev]
                prev = None
            else:
                px += adv[b]
                prev = b
            i += 1
    return px


def marker_positions(raw: bytes) -> list[int]:
    """Posiciones de 0xDE/0xDF sueltos (no 2º byte de un par SJIS) que siguen a un carácter de la misma línea."""
    out, i, prev = [], 0, None
    while i < len(raw):
        b = raw[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(raw):
            prev, i = b, i + 2
            continue
        if b in MARKERS and prev is not None and prev != 0x0A:
            out.append(i)
        prev, i = b, i + 1
    return out


# ───────────────────────────── Lectura de volcados ─────────────────────────────
DEADMESS_PREFIX = ': '     # lo que el juego pone entre el nombre y la frase de DEADMESS (SNMP_GRP +0x5B0; era 「, y 」 al final: quitados, ver layout_patch.py)


def pilot_short_names() -> dict:
    """id → nombre corto que muestra el juego (inglés si ya está traducido); vacío si no hay dump."""
    path = WORK / 'dump' / 'pilot.jsonl'
    if not path.exists():
        return {}
    out = {}
    for line in open(path, encoding='utf-8'):
        if line.strip():
            r = json.loads(line)
            out[r['id']] = r.get('short_en') or r.get('short', '')
    return out


def dict_field_max(fmt: str, rec_id: int, off: int) -> int:
    """Tope de bytes de un campo de DC/DR según el layout confirmado (option_dict.LAYOUT)."""
    from option_dict import LAYOUT, LINE_MAX, INDEX_MAX
    if rec_id == 0:
        return INDEX_MAX
    head = dict(LAYOUT[fmt]['fields'])
    return head[off] - 1 if off in head else LINE_MAX


def iter_rows(fmt: str, path: Path):
    """Filas (clave, jp, en, tope_de_bytes_propio, reserva_px (renglón 1, último)). En DC/DR cada campo es una fila."""
    names = pilot_short_names() if fmt == 'deadmess' else {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if fmt in ('dc', 'dr'):
                fields = r.get('fields', [])
                en_list = r.get('en') if isinstance(r.get('en'), list) else None
                for k, fd in enumerate(fields):
                    en = fd.get('en') or (en_list[k] if en_list and k < len(en_list) else '')
                    yield (f"{r['id']}@{fd['off']}", fd['text'], en or '', dict_field_max(fmt, r['id'], fd['off']),
                           (0, 0))
            else:
                key = {'snmsg': ('id',), 'script': ('script', 'inst'), 'bxclist': ('pilot', 'idx'),
                       'deadmess': ('slot',), 'em': ('rec',), 'mdata': ('file', 'off')}[fmt]
                reserve = (0, 0)
                if fmt == 'bxclist':            # sin 「」 desde que se quitaron (BTL_GRP)
                    reserve = (0, 0)
                if fmt == 'deadmess':
                    name = names.get(r['pilot'], '')
                    reserve = ((line_px(name, 12) if name else 0) + line_px(DEADMESS_PREFIX, 12), 0)
                # en_ref (fork, kit.py pivot): el builder lo usa si falta en → se valida lo que se va a ver
                yield ('/'.join(str(r[k]) for k in key), r.get('jp', ''), r.get('en') or r.get('en_ref') or '', None,
                       reserve)


# ───────────────────────────── Validación ─────────────────────────────
def check_text(en: str, jp: str, f: Fmt, max_bytes: int | None = None, reserve: tuple = (0, 0)) -> list[dict]:
    """Violaciones de un texto: lista de {kind, line, value, limit, severity, detail}.
    reserve = px que el juego ocupa en el renglón 1 y en el último (p. ej. nombre「 y 」 en DEADMESS)."""
    out = []

    def add(kind, value, limit, line='', detail='', limit_name=None):
        sev = 'warn' if (limit_name or kind) in f.assumed else 'error'
        out.append({'kind': kind, 'line': line, 'value': value, 'limit': limit, 'severity': sev, 'detail': detail})

    try:
        raw = encode(to_game(en))
    except UnicodeEncodeError as e:
        add('encoding', repr(e.object[e.start:e.end]), 'cp932', detail='carácter sin equivalente en Shift-JIS')
        return out
    except ValueError as e:
        add('encoding', str(e), 'cp932')
        return out
    cap = max_bytes if max_bytes is not None else f.max_bytes
    if cap is not None and len(raw) > cap:
        add('bytes', len(raw), cap)
    lines = en.split('\n')
    if f.max_lines is not None and len(lines) > f.max_lines:
        add('lines', len(lines), f.max_lines)
    if f.line_px is not None:
        for n, ln in enumerate(lines, 1):
            w = line_px(ln, f.kana_px)
            lim = f.line_px - (reserve[0] if n == 1 else 0) - (reserve[1] if n == len(lines) else 0)
            if w > lim:
                add('px', w, lim, line=n, detail=ln)
    if is_choice(jp) and len(lines) != jp.count('\n') + 1:
        add('choice', len(lines), jp.count('\n') + 1, detail='decisión: una línea por opción, igual que "jp"')
    if Counter(VAR.findall(en)) != Counter(VAR.findall(jp)):
        out.append({'kind': 'placeholder', 'line': '', 'severity': 'error',
                    'value': ' '.join(sorted(VAR.findall(en))) or '-',
                    'limit': ' '.join(sorted(VAR.findall(jp))) or '-', 'detail': 'variables distintas a "jp"'})
    for pos in marker_positions(raw):
        out.append({'kind': 'marker', 'line': raw[:pos].count(b'\n') + 1, 'severity': 'error',
                    'value': f'0x{raw[pos]:02X}@{pos}', 'limit': '-', 'detail': 'ﾞ/ﾟ tras un carácter = glifo especial'})
    if f.speaker:
        for d in speaker_issues(en, jp):
            out.append({'kind': 'speaker', 'line': '', 'severity': 'warn', 'value': '', 'limit': 'Nombre: texto',
                        'detail': d})
    if ' ' in en and ('  ' in en or en != en.strip()):
        out.append({'kind': 'spaces', 'line': '', 'severity': 'warn', 'value': '', 'limit': '',
                    'detail': 'espacios dobles o al borde (ocupan px)'})
    return out


# ───────────────────────────── Ajuste de línea (--wrap) ─────────────────────────────
def wrap(en: str, width: int, kana_px: int = 12, keep_breaks: bool = False) -> list[str]:
    """Reparte las palabras en líneas de hasta `width` px (codicioso). Sin keep_breaks, re-fluye todo el texto."""
    paras = en.split('\n') if keep_breaks else [' '.join(en.split('\n'))]
    out = []
    for p in paras:
        cur = ''
        for word in p.split():
            cand = f'{cur} {word}' if cur else word
            if line_px(cand, kana_px) <= width:
                cur = cand
                continue
            if cur:
                out.append(cur)
            cur = word
            while line_px(cur, kana_px) > width and len(cur) > 1:   # palabra más ancha que la caja: se corta
                k = len(cur)
                while k > 1 and line_px(cur[:k], kana_px) > width:
                    k -= 1
                out.append(cur[:k])
                cur = cur[k:]
        out.append(cur)
    return out


# ───────────────────────────── Programa ─────────────────────────────
CSV_FIELDS = ['format', 'id', 'kind', 'severity', 'line', 'value', 'limit', 'detail', 'en']


def run(formats, inputs, csv_path, wrap_path, keep_breaks):
    rows_out, wraps, summary = [], [], {}
    for name in formats:
        f = FORMATS[name]
        path = inputs.get(name) or WORK / 'dump' / f.file
        if not path.exists():
            print(f'[{name}] no existe {path}: se omite', file=sys.stderr)
            continue
        total = translated = 0
        kinds = Counter()
        for key, jp, en, own_cap, reserve in iter_rows(name, path):
            total += 1
            if not en:
                continue
            translated += 1
            viol = check_text(en, jp, f, own_cap, reserve)
            for v in viol:
                kinds[(v['kind'], v['severity'])] += 1
                rows_out.append({'format': name, 'id': key, **v, 'en': en})
            if wrap_path and f.line_px and any(v['kind'] in ('px', 'lines') for v in viol):
                w = wrap(en, f.line_px, f.kana_px, keep_breaks)
                wraps.append({'format': name, 'id': key, 'en': en, 'en_wrapped': '\n'.join(w), 'lines': len(w),
                              'fits': f.max_lines is None or len(w) <= f.max_lines})
        summary[name] = (total, translated, kinds)

    if csv_path:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w', encoding='utf-8', newline='') as fh:
            wr = csv.DictWriter(fh, CSV_FIELDS)
            wr.writeheader()
            wr.writerows(rows_out)
    if wrap_path:
        wrap_path.parent.mkdir(parents=True, exist_ok=True)
        with open(wrap_path, 'w', encoding='utf-8') as fh:
            fh.writelines(json.dumps(w, ensure_ascii=False) + '\n' for w in wraps)

    print(f'Tabla de anchos: {ADV_SRC}')
    print(f'{"formato":9} {"filas":>7} {"trad.":>7} {"errores":>8} {"avisos":>7}  detalle')
    n_err = 0
    for name, (total, translated, kinds) in summary.items():
        e = sum(c for (k, s), c in kinds.items() if s == 'error')
        w = sum(c for (k, s), c in kinds.items() if s == 'warn')
        n_err += e
        det = ', '.join(f'{k}:{c}{"?" if s == "warn" else ""}' for (k, s), c in sorted(kinds.items()))
        print(f'{name:9} {total:7} {translated:7} {e:8} {w:7}  {det}')
    if csv_path:
        print(f'{len(rows_out)} violaciones → {csv_path}')
    if wrap_path:
        print(f'{len(wraps)} propuestas de salto de línea ({sum(not w["fits"] for w in wraps)} siguen sin entrar) → {wrap_path}')
    return n_err


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', help='formatos separados por coma (por defecto todos: ' + ','.join(FORMATS) + ')')
    ap.add_argument('--input', action='append', default=[], metavar='FMT=RUTA',
                    help='otro JSONL para un formato (p. ej. dc=translation/dc_en.jsonl)')
    ap.add_argument('--csv', type=Path, default=WORK / 'build' / 'check_text.csv')
    ap.add_argument('--wrap', type=Path, metavar='SALIDA.jsonl', help='proponer saltos para lo que no entra')
    ap.add_argument('--keep-breaks', action='store_true', help='--wrap: respetar los \\n existentes')
    ap.add_argument('--wrap-text', metavar='TEXTO', help='ajustar un texto suelto e imprimir el resultado')
    ap.add_argument('--format', default='snmsg', choices=FORMATS, help='formato para --wrap-text')
    a = ap.parse_args(argv)

    if a.wrap_text is not None:
        f = FORMATS[a.format]
        width = f.line_px or 240
        for ln in wrap(a.wrap_text.replace('\\n', '\n'), width, f.kana_px, a.keep_breaks):
            print(f'{line_px(ln, f.kana_px):4} px | {ln}')
        return 0

    formats = a.only.split(',') if a.only else list(FORMATS)
    bad = [x for x in formats if x not in FORMATS]
    if bad:
        ap.error(f'formato desconocido: {bad}')
    inputs = {}
    for item in a.input:
        k, _, v = item.partition('=')
        if k not in FORMATS or not v:
            ap.error(f'--input inválido: {item}')
        inputs[k] = Path(v)
    return 1 if run(formats, inputs, a.csv, a.wrap, a.keep_breaks) else 0


if __name__ == '__main__':
    sys.exit(main())
