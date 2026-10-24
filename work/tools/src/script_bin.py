"""BUSTUP/SCRIPT.BIN (escenas de intermisión): extracción y reconstrucción.

Formato (verificado 2026-09-27: los 255 scripts se recorren exactos de punta a punta):
  u32 offset[255] absolutos · scripts consecutivos
  instrucción: u16 op · u16 sub · u16 arg · u16 len · len bytes de datos · relleno hasta múltiplo de 4
  (el relleno trae basura del compilador, p. ej. "00 d4 41": se conserva para reconstruir byte a byte)
  op 0x0010 = línea de texto SJIS terminada en NUL (0x0A = salto de línea; $n = nombre del protagonista)
  op 0x0210 = línea hablada del protagonista (mismo formato que 0x0010, otro flag; 281 líneas)  [#220]
  op 0x0080 = menú de decisión: opciones `「…」` separadas por 0x0A (68 en 61 escenas; la caja de opciones
              no es la de diálogo: ancho a medir)  [#220]
  No se encontraron saltos: ningún op tiene argumentos que caigan sistemáticamente en inicios de instrucción,
  así que cambiar el largo de un texto solo exige recalcular len, el relleno y la tabla de offsets.
Uso:
  script_bin.py dump [salida.jsonl]            → una línea JSON por texto (script, idx, sub, jp)
  script_bin.py build entrada.jsonl salida.BIN  → reconstruye usando el campo "en" cuando no está vacío (o "en_ref")
  script_bin.py selftest                         → reconstrucción sin cambios == original
"""
import json, os, struct, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(WORK, 'iso_jp', 'BUSTUP', 'SCRIPT.BIN')
NSCRIPTS = 255
TEXT_OP = 0x0010           # línea de diálogo "clásica": el único op con numeración `line` (estable, #220)
CHOICE_OP = 0x0080         # menú de decisión (sub 1 o 2)
SPOKEN_OP = 0x0210         # línea hablada del protagonista
TEXT_OPS = (TEXT_OP, SPOKEN_OP, CHOICE_OP)


def parse(data):
    offs = list(struct.unpack_from('<%dI' % NSCRIPTS, data, 0)) + [len(data)]
    scripts = []
    for k in range(NSCRIPTS):
        p, end, insts = offs[k], offs[k + 1], []
        while p + 8 <= end:
            op, sub, arg, ln = struct.unpack_from('<4H', data, p)
            body = data[p + 8:p + 8 + ln]
            padded = (ln + 3) & ~3
            pad = data[p + 8 + ln:p + 8 + padded]
            insts.append({'op': op, 'sub': sub, 'arg': arg, 'data': body, 'pad': pad})
            p += 8 + padded
        assert p == end, f'script {k}: termina en {p:#x}, se esperaba {end:#x}'
        scripts.append(insts)
    header = data[:offs[0]] if offs[0] > 4 * NSCRIPTS else b''
    return scripts, header, offs[0]


def build(scripts, first_off, header_tail=b''):
    blobs = []
    for insts in scripts:
        out = bytearray()
        for ins in insts:
            body = ins['data']
            padded = (len(body) + 3) & ~3
            pad = ins['pad'] if len(ins['pad']) == padded - len(body) else b'\0' * (padded - len(body))
            out += struct.pack('<4H', ins['op'], ins['sub'], ins['arg'], len(body)) + body + pad
        blobs.append(bytes(out))
    table_size = first_off
    offs, cur = [], table_size
    for b in blobs:
        offs.append(cur); cur += len(b)
    head = struct.pack('<%dI' % NSCRIPTS, *offs)
    head += header_tail[len(head):table_size] if len(header_tail) >= table_size else b'\0' * (table_size - len(head))
    return head + b''.join(blobs)


def is_text(ins):
    """op 0x10 siempre es texto; 0x210/0x80 solo si el cuerpo es SJIS con NUL (hay instrucciones 0x80 sin texto)."""
    if ins['op'] == TEXT_OP:
        return True
    d = ins['data']
    if not d or d.find(b'\0') < 0:
        return False
    try:
        t = d.split(b'\0')[0].decode('cp932')
    except UnicodeDecodeError:
        return False
    return any(0x3040 <= ord(c) <= 0x9fff or 0xff00 <= ord(c) for c in t)


def texts(scripts):
    for k, insts in enumerate(scripts):
        n = 0
        for i, ins in enumerate(insts):
            if ins['op'] in TEXT_OPS and is_text(ins):
                yield k, i, n, ins
                if ins['op'] == TEXT_OP:
                    n += 1


def encode_en(s):
    """Inglés → bytes del juego: espacio = 0xA0 (ver notes/fuente_en.md), salto de línea = 0x0A."""
    return s.encode('cp932').replace(b' ', b'\xa0') + b'\0'


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'selftest'
    data = open(SRC, 'rb').read()
    scripts, _, first = parse(data)
    if cmd == 'selftest':
        again = build(scripts, first, data)
        print('reconstrucción idéntica:', again == data, f'({len(again)} bytes)')
    elif cmd == 'dump':
        dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, 'dump', 'script.jsonl')
        n = 0
        with open(dst, 'w', encoding='utf-8') as f:
            for k, i, t, ins in texts(scripts):
                jp = ins['data'].split(b'\0')[0].decode('cp932', 'replace')
                row = {'script': k, 'inst': i, 'line': t, 'sub': ins['sub'], 'jp': jp, 'en': ''}
                if ins['op'] != TEXT_OP:
                    row['op'] = ins['op']        # solo 0x210 / 0x80 (#220); las 0x10 quedan idénticas a antes
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
                n += 1
        print(n, 'líneas →', dst)
    elif cmd == 'build':
        src, dst = sys.argv[2], sys.argv[3]
        changed = 0
        for line in open(src, encoding='utf-8'):
            r = json.loads(line)
            en = r.get('en') or r.get('en_ref')     # en_ref: inglés de referencia de un fork (kit.py pivot)
            if en:
                ins = scripts[r['script']][r['inst']]
                assert ins['op'] in TEXT_OPS and r.get('op', TEXT_OP) == ins['op']
                ins['data'] = encode_en(en)
                changed += 1
        import mapa_lugares                      # rótulos de lugar del mapa 「現在位置」: cajas del inglés (#188)
        places = mapa_lugares.patch_script(scripts)
        open(dst, 'wb').write(build(scripts, first, data))
        print(changed, 'líneas reemplazadas,', places, 'rótulos de lugar →', dst)


if __name__ == '__main__':
    main()
