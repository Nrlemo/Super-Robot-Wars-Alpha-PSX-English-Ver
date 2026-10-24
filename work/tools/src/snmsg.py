"""Dump / rebuild de SNMAP/SNMSG.BIN (32.544 slots fijos de 256 bytes, SJIS, relleno 00).

  snmsg.py dump  <SNMSG_jp.BIN> <SNMSG_chs.BIN|-> <salida.jsonl>   (- = sin el parche chino: "chs" vacío)
  snmsg.py build <entrada.jsonl> <SNMSG_out.BIN>
  snmsg.py check <SNMSG_jp.BIN> <entrada.jsonl>     # rebuild sin traducciones == original

JSONL, un slot por línea (diff-friendly en git):
  {"id": 123, "speaker": "甲児", "jp": "...", "chs": "...", "en": "", "notes": ""}
En build se usa "en" si no está vacío; si no, "en_ref" (fork que traduce desde el inglés, kit.py pivot); si no, "jp".
"""
import json
import re
import sys
from pathlib import Path

from sjis_text import decode, encode

SLOT = 256
MAX_BYTES = SLOT - 1  # al menos un 00 terminador
MAX_LINES = 3
# Caja de 240 px (medido en emulador, notes/poc_snmsg.md). Maquetado en FUN_80018CC4 (notes/vwf_investigacion.md):
#   byte simple → avance = tabla VWF (patches/vwf_table.bin, 8 px sin parche); SJIS → 12 px;
#   hiragana/katakana SJIS en el diálogo de mapa (flags=3) → 8 px.
# Si x + avance > 240 el motor salta de línea solo; como solo se ven 3 líneas, se valida por píxeles.
LINE_PX = 240
# Reserva por variable, igual que check_text.py (notes/nombres_protagonistas.md): apodo ≤ 8 letras × 6 px,
# nombre ≤ 8, apellido ≤ 9 (valor por defecto "Luckfield"), nombre completo 8 + espacio + 9.
VAR_PX = {'n': 48, 'N': 48, 'm': 48, 'M': 48, 's': 54, 'S': 54, 'f': 108, 'F': 108}
NAME_VAR_PX = VAR_PX['n']
VWF_TABLE = Path(__file__).resolve().parents[2] / 'patches' / 'vwf_table.bin'
ADV = VWF_TABLE.read_bytes() if VWF_TABLE.exists() else bytes([8] * 256)
_SPEAKER = re.compile(r'^([^「（\n]{1,12})[「（]')
_VAR = re.compile(r'\$[nNfFmMsS]')


EN_SPACE = '{A0}'  # espacio angosto del texto inglés (0x20 queda en 8 px para la alineación de menús)


def en_to_game(text: str) -> str:
    """Texto inglés → texto del juego: espacios a 0xA0 (notes/fuente_en.md)."""
    return text.replace(' ', EN_SPACE)


def line_px(line: str) -> int:
    """Ancho en px de una línea (texto del juego, con escapes {XX}) según el maquetador FUN_80018CC4."""
    px = sum(VAR_PX[v[1]] for v in _VAR.findall(line))
    raw, i = encode(_VAR.sub('', line)), 0
    while i < len(raw):
        b = raw[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(raw):
            code = (b << 8) | raw[i + 1]
            px += 8 if 0x829F <= code <= 0x82F1 or 0x8340 <= code <= 0x8396 else 12
            i += 2
        else:
            px += ADV[b]
            i += 1
    return px


def split_slots(data: bytes) -> list[bytes]:
    assert len(data) % SLOT == 0, 'tamaño no múltiplo de 256'
    return [data[i:i + SLOT].rstrip(b'\x00') for i in range(0, len(data), SLOT)]


def dump(jp_path, chs_path, out_path):
    jp = split_slots(Path(jp_path).read_bytes())
    chs = split_slots(Path(chs_path).read_bytes()) if chs_path != '-' else jp   # igual al jp → "chs" vacío
    with open(out_path, 'w', encoding='utf-8') as f:
        for i, (a, b) in enumerate(zip(jp, chs)):
            text = decode(a)
            m = _SPEAKER.match(text)
            row = {'id': i, 'speaker': m.group(1) if m else '', 'jp': text,
                   # el juego lee hasta el primer 00: lo que sigue en CHS es basura
                   'chs': decode(b.split(b'\x00')[0]) if b != a else '', 'en': '', 'notes': ''}
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f'{len(jp)} slots → {out_path}')


def load(jsonl_path) -> list[dict]:
    with open(jsonl_path, encoding='utf-8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
    assert [r['id'] for r in rows] == list(range(len(rows))), 'ids faltantes o desordenados'
    return rows


def build(jsonl_path, out_path) -> bytes:
    out, errors = bytearray(), []
    for r in load(jsonl_path):
        en = r['en'] or r.get('en_ref', '')    # en_ref: inglés de referencia de un fork (kit.py pivot)
        text = en_to_game(en) if en else r['jp']
        try:
            raw = encode(text)
        except UnicodeEncodeError as e:
            errors.append(f"slot {r['id']}: carácter no codificable {e.object[e.start:e.end]!r}")
            raw = encode(r['jp'])
        if len(raw) > MAX_BYTES:
            errors.append(f"slot {r['id']}: {len(raw)} bytes > {MAX_BYTES}")
            raw = encode(r['jp'])
        if en:
            lines = text.split('\n')
            if len(lines) > MAX_LINES:
                errors.append(f"slot {r['id']}: {len(lines)} líneas > {MAX_LINES}")
            for n, ln in enumerate(lines, 1):
                if line_px(ln) > LINE_PX:
                    errors.append(f"slot {r['id']} línea {n}: {line_px(ln)} px (máx {LINE_PX}): {ln!r}")
        out += raw.ljust(SLOT, b'\x00')
    for e in errors:
        print('ERROR', e, file=sys.stderr)
    if out_path:
        Path(out_path).write_bytes(out)
        print(f'{len(out) // SLOT} slots → {out_path} ({len(errors)} errores)')
    return bytes(out)


def check(jp_path, jsonl_path):
    orig = Path(jp_path).read_bytes()
    rows = load(jsonl_path)
    for r in rows:
        r['en'] = ''
        r.pop('en_ref', None)
    tmp = Path(jsonl_path).with_suffix('.check.tmp')
    tmp.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    try:
        rebuilt = build(tmp, None)
    finally:
        tmp.unlink()
    ok = rebuilt == orig
    print('round-trip byte-idéntico:', ok)
    return ok


if __name__ == '__main__':
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ('', [])
    if cmd == 'dump' and len(args) == 3:
        dump(*args)
    elif cmd == 'build' and len(args) == 2:
        build(*args)
    elif cmd == 'check' and len(args) == 2:
        sys.exit(0 if check(*args) else 1)
    else:
        sys.exit(__doc__)
