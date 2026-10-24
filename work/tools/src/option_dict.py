"""OPTION/DC.BIN (personajes) y OPTION/DR.BIN (robots): volcado de texto y reempaquetado en inglés.

Contenedor: u32 offset[n] absolutos (el primero = tamaño de la tabla), alineados a 4 → entrada: u32 tamaño, u32 0,
LZSS (ver robot_raf.py y notes/compresion.md). Entrada 0 = índice de nombres; la última está vacía.

Registro (layout confirmado en las 349/448 fichas: tamaño = base + cantidad × 48; notes/diccionarios_traduccion.md):
  DC  +0x00 nombre (48) · +0x30 corto (20) · +0x44 serie (64) · +0x84 seiyuu (20) · +0x98 u32 cantidad de líneas ·
      +0x9C líneas de 48 bytes
  DR  +0x00 nombre (48) · +0x30 altura (32) · +0x50 peso (32) · +0x70 serie (64) · +0xB0 u32 cantidad · +0xB4 líneas
Campos de cabecera: texto, NUL, relleno 0xCD. Líneas: texto, NUL NUL, relleno 0xCD. Índice: casilleros de 48 bytes
(texto, NUL, 0xCD…, NUL final).

Uso:
  option_dict.py [dump]                        → dump/dc.jsonl, dump/dr.jsonl
  option_dict.py build dc|dr JSONL SALIDA      → DC.BIN/DR.BIN con el campo `en` (lista paralela a `fields`)
  option_dict.py selftest                      → build sin inglés = archivo original byte a byte; ida y vuelta de
                                                 translation/*_en.jsonl
"""
import json, os, re, struct, sys
from robot_raf import lzss, pack_entry, to_game, WORK

LAYOUT = {  # campos de cabecera (offset, tamaño), offset del u32 cantidad, base de las líneas
    'dc': {'fields': [(0x00, 48), (0x30, 20), (0x44, 64), (0x84, 20)], 'count': 0x98, 'lines': 0x9C},
    'dr': {'fields': [(0x00, 48), (0x30, 32), (0x50, 32), (0x70, 64)], 'count': 0xB0, 'lines': 0xB4},
}
LINE = 48
LINE_MAX = LINE - 2          # texto de una línea: ≤46 bytes + NUL NUL
INDEX_SLOT = 48
INDEX_MAX = INDEX_SLOT - 2   # texto, NUL y el NUL final del casillero


def iso_path(fmt):
    return os.path.join(WORK, 'iso_jp', 'OPTION', fmt.upper() + '.BIN')


def chunks(d):
    n = struct.unpack_from('<I', d, 0)[0] // 4
    offs = struct.unpack_from('<%dI' % n, d, 0)
    return [d[offs[i]:offs[i + 1] if i + 1 < n else len(d)] for i in range(n)]


def unpack(c):
    return lzss(c[8:], struct.unpack_from('<I', c, 0)[0]) if len(c) >= 8 else b''


def entries(path):
    for i, c in enumerate(chunks(open(path, 'rb').read())):
        yield i, unpack(c)


def fields(raw):
    """Strings entre separadores (NUL o 0xCD suelto), recorriendo SJIS: 0xCD puede ser 2º byte de un kanji."""
    out, cur, start, i = [], bytearray(), 0, 0
    def flush():
        if len(cur) >= 2:
            try:
                s = cur.decode('cp932')
            except UnicodeDecodeError:
                s = ''
            if re.search(r'[぀-ヿ一-鿿ｦ-ﾟ0-9A-Za-z]', s):
                out.append({'off': start, 'text': s})
    while i < len(raw):
        b = raw[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(raw) and b != 0xCD:
            if not cur: start = i
            cur += raw[i:i + 2]; i += 2
        elif b in (0x00, 0xCD):
            flush(); cur.clear(); i += 1
        else:
            if not cur: start = i
            cur.append(b); i += 1
    flush()
    return out


def dump():
    for fmt in ('dc', 'dr'):
        dst = os.path.join(WORK, 'dump', fmt + '.jsonl')
        n = chars = 0
        with open(dst, 'w', encoding='utf-8') as f:
            for i, raw in entries(iso_path(fmt)):
                fs = fields(raw)
                f.write(json.dumps({'id': i, 'size': len(raw), 'fields': fs}, ensure_ascii=False) + '\n')
                n += 1; chars += sum(len(x['text']) for x in fs)
        print(f'{fmt.upper()}: {n} entradas, {chars} caracteres de texto → {dst}')


# ───────────────────────────── Reempaquetado ─────────────────────────────
class FitError(ValueError):
    pass


def put(rec, off, size, text, tail=b'\0', where=''):
    raw = to_game(text)
    if len(raw) + len(tail) > size:
        raise FitError(f'{where}: {len(raw)} bytes, tope {size - len(tail)}: {text!r}')
    rec[off:off + size] = raw + tail + b'\xcd' * (size - len(raw) - len(tail))


def build_index(raw, rec_json, where):
    rec = bytearray(raw)
    for fd, en in zip(rec_json['fields'], rec_json.get('en') or []):
        if not en:
            continue
        off = fd['off']
        if off % INDEX_SLOT:
            raise FitError(f'{where}@{off}: casillero del índice desalineado')
        put(rec, off, INDEX_SLOT - 1, en, where=f'{where}@{off}')
        rec[off + INDEX_SLOT - 1] = 0
    return bytes(rec)


def build_record(fmt, raw, rec_json, where):
    """Registro inglés: cabecera in situ; líneas desde la base, sin las líneas vacías del final (baja la cantidad)."""
    lay = LAYOUT[fmt]
    head = {off: size for off, size in lay['fields']}
    base = lay['lines']
    count = struct.unpack_from('<I', raw, lay['count'])[0]
    if base + count * LINE != len(raw):
        raise FitError(f'{where}: layout inesperado ({len(raw)} bytes, {count} líneas)')
    rec = bytearray(raw)
    lines = {}
    for fd, en in zip(rec_json['fields'], rec_json.get('en') or []):
        off = fd['off']
        if off in head:
            if en:
                put(rec, off, head[off], en, where=f'{where}@{off}')
        elif off >= base and (off - base) % LINE == 0:
            lines[(off - base) // LINE] = en or ''
        else:
            raise FitError(f'{where}@{off}: campo fuera del layout')
    if not lines:
        return bytes(rec)
    for k, text in lines.items():            # "" intermedio = renglón en blanco
        put(rec, base + k * LINE, LINE, text, tail=b'\0\0', where=f'{where}@{base + k * LINE}')
    new_count = max((k for k, t in lines.items() if t), default=count - 1) + 1
    del rec[base + new_count * LINE:]
    struct.pack_into('<I', rec, lay['count'], new_count)
    return bytes(rec)


def build(fmt, jsonl, out=None):
    """Devuelve (bytes del archivo, estadísticas). Si una ficha no cambia se copia el bloque comprimido original."""
    orig = open(iso_path(fmt), 'rb').read()
    old = chunks(orig)
    recs = {}
    if jsonl:
        for line in open(jsonl, encoding='utf-8'):
            if line.strip():
                r = json.loads(line)
                recs[r['id']] = r
    new, changed, errors = [], 0, []
    for i, c in enumerate(old):
        raw = unpack(c)
        r = recs.get(i)
        if r is None or not raw or not any(r.get('en') or []):
            new.append(c)
            continue
        try:
            nraw = build_index(raw, r, f'{fmt}{i}') if i == 0 else build_record(fmt, raw, r, f'{fmt}{i}')
        except FitError as e:
            errors.append(str(e)); new.append(c); continue
        if nraw == raw:
            new.append(c)
        else:
            new.append(pack_entry(nraw)); changed += 1
    table = 4 * len(new)
    offs, cur = [], table
    for c in new:
        offs.append(cur); cur += (len(c) + 3) & ~3
    data = struct.pack('<%dI' % len(new), *offs) + b''.join(c + b'\0' * (-len(c) % 4) for c in new)
    if out:
        with open(out, 'wb') as f:
            f.write(data)
    return data, {'entradas': len(new), 'cambiadas': changed, 'errores': errors}


def roundtrip(fmt, data, jsonl):
    """Relee el archivo construido y compara cada campo con el inglés esperado."""
    got = [unpack(c) for c in chunks(data)]
    bad = 0
    for line in open(jsonl, encoding='utf-8'):
        r = json.loads(line)
        raw = got[r['id']]
        for fd, en in zip(r['fields'], r.get('en') or []):
            if not en:
                continue
            if fd['off'] >= len(raw) or raw[fd['off']:].split(b'\0')[0] != to_game(en):
                bad += 1
                print(f'  DIFERENCIA {fmt}{r["id"]}@{fd["off"]}: {en!r}')
    return bad


def selftest():
    ok = True
    for fmt in ('dc', 'dr'):
        orig = open(iso_path(fmt), 'rb').read()
        data, _ = build(fmt, None)
        same = data == orig
        jsonl = os.path.join(WORK, 'translation', fmt + '_en.jsonl')
        data, st = build(fmt, jsonl)
        bad = roundtrip(fmt, data, jsonl)
        print(f'{fmt}: sin inglés = original: {same} · con inglés: {st["cambiadas"]}/{st["entradas"]} fichas, '
              f'{len(st["errores"])} errores, {bad} diferencias en la relectura')
        ok &= same and not st['errores'] and not bad
    print('selftest OK' if ok else 'selftest FALLÓ')
    return ok


def main(argv):
    cmd = argv[0] if argv else 'dump'
    if cmd == 'dump':
        dump()
    elif cmd == 'build':
        fmt, jsonl, out = argv[1], argv[2], argv[3]
        _, st = build(fmt, jsonl, out)
        for e in st['errores']:
            print('ERROR', e)
        print(f'{fmt.upper()}: {st["cambiadas"]}/{st["entradas"]} fichas en inglés → {out}'
              + (f' · {len(st["errores"])} errores (quedan en japonés)' if st['errores'] else ''))
        return 1 if st['errores'] else 0
    elif cmd == 'selftest':
        return 0 if selftest() else 1
    else:
        print(__doc__); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
