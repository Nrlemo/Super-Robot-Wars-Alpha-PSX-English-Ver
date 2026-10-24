"""SNMAP/MDATA.BIN y TEST/MDATA.BIN (datos de mapa): nombres de terreno y lugares (#221).

Formato (verificado 2026-10-01 sobre los 140 bloques de SNMAP y los 11 de TEST):
  u32 offset[...] absolutos, múltiplos de 0x800: un bloque por mapa; el último valor = tamaño del archivo
  dentro de cada bloque, registros de 20 bytes alineados a 4: u8[4] cabecera + char name[16] (SJIS, relleno NUL).
  Nombres: terrenos (領域外, 平原, 道路…), lugares (光子力研究所, 兜甲児の家…) y fragmentos que el motor une (電力供給 + ﾋﾞﾙ).
  Un nombre ocupa a lo sumo 14 bytes en japonés; el campo tiene 16 → inglés ≤ 15 caracteres + NUL.
  No hay punteros a los nombres: se reemplazan en el mismo lugar (el archivo no cambia de tamaño).
Uso:
  mdata_bin.py dump [salida.jsonl]            → una línea JSON por nombre (file, off, jp, en)
  mdata_bin.py build SNMAP|TEST entrada.jsonl salida.BIN   → aplica "en" (o "en_ref") si no está vacío a ese archivo
  mdata_bin.py selftest                        → reconstrucción sin cambios == original
"""
import json, os, re, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FILES = {'SNMAP': os.path.join(WORK, 'iso_jp', 'SNMAP', 'MDATA.BIN'),
         'TEST': os.path.join(WORK, 'iso_jp', 'TEST', 'MDATA.BIN')}
FIELD = 16
FULLWIDTH = re.compile(r'[ぁ-んァ-ヴ一-龥]')
HALF_ONLY = re.compile(r'[ｦ-ﾟ!-~]+')   # nombres solo en kana de ancho medio y ASCII (ﾏｸﾛｽﾄﾞｯｸ, ｺﾛﾆ-): ≥3 kana y 2 NUL al final
# 1+ caracteres SJIS (dobles o kana de ancho medio) seguidos solo de NUL hasta completar el campo de 16 bytes
FIELD_RX = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\xa1-\xdf]|[\x21-\x7e])+\0*')


def encode_en(s):
    """Inglés → bytes del juego (espacio = 0xA0, ver notes/fuente_en.md), relleno NUL hasta 16."""
    b = s.encode('cp932').replace(b' ', b'\xa0')
    if len(b) > FIELD - 1:
        raise ValueError(f'{s!r}: {len(b)} bytes, tope {FIELD - 1}')
    return b + b'\0' * (FIELD - len(b))


def fields(data):
    """(offset, texto_jp) de cada campo de nombre: alineado a 4, 16 bytes, al menos un carácter de ancho completo."""
    out, p = [], 4
    while p <= len(data) - FIELD:
        raw = data[p:p + FIELD]
        t = None
        if raw[0] != 0 and FIELD_RX.fullmatch(raw) and raw[-1] == 0:
            try:
                t = raw.rstrip(b'\0').decode('cp932')
            except UnicodeDecodeError:
                pass
        if t and (FULLWIDTH.search(t) or (HALF_ONLY.fullmatch(t) and len(re.findall(r'[ｦ-ﾟ]', t)) >= 3 and raw[-2] == 0)):
            out.append((p, t))
            p += FIELD            # el campo entero: sus sufijos alineados a 4 no son nombres (外 dentro de 領域外)
        else:
            p += 4
    return out


def dump_rows():
    rows = []
    for name, path in FILES.items():
        for off, jp in fields(open(path, 'rb').read()):
            rows.append({'file': name, 'off': off, 'jp': jp, 'en': ''})
    return rows


def build(data, rows):
    out, n = bytearray(data), 0
    for r in rows:
        en = r.get('en') or r.get('en_ref')         # en_ref: inglés de referencia de un fork (kit.py pivot)
        if en:
            assert out[r['off']:r['off'] + FIELD].rstrip(b'\0').decode('cp932') == r['jp'], f'{r["file"]}:{r["off"]:#x} no coincide'
            out[r['off']:r['off'] + FIELD] = encode_en(en)
            n += 1
    return bytes(out), n


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'selftest'
    if cmd == 'selftest':
        for name, path in FILES.items():
            data = open(path, 'rb').read()
            rows = [{'file': name, 'off': o, 'jp': t, 'en': t} for o, t in fields(data) if all(ord(c) < 0x10000 for c in t)]
            print(name, len(rows), 'campos;', 'sin traducción → idéntico:', build(data, []) [0] == data)
    elif cmd == 'dump':
        dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, 'dump', 'mdata.jsonl')
        rows = dump_rows()
        with open(dst, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(len(rows), 'nombres →', dst)
    elif cmd == 'build':
        name, src, dst = sys.argv[2], sys.argv[3], sys.argv[4]
        rows = [r for r in (json.loads(l) for l in open(src, encoding='utf-8')) if r['file'] == name]
        data, n = build(open(FILES[name], 'rb').read(), rows)
        open(dst, 'wb').write(data)
        print(name, n, 'nombres reemplazados →', dst)


if __name__ == '__main__':
    main()
