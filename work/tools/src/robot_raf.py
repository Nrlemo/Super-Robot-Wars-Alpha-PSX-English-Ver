"""UNITPRAM/ROBOT.RAF: descompresión (LZSS) y volcado de unidades y armas.

Formato (verificado 2026-09-27 contra el registro de Excelion descomprimido en RAM, 0x80138234):
  u32 n (486) · u32 offset[n] (relativos al fin de la tabla) · entradas
  entrada: u32 tamaño descomprimido · u32 (0) · datos LZSS
  LZSS estilo Okumura: byte de banderas por cada 8 elementos (LSB primero; 1 = literal, 0 = referencia de 2 bytes),
  referencia: pos = b1 | (b2 & 0xF0) << 4, largo = (b2 & 0x0F) + 3; anillo de 4096 bytes en cero, escritura desde 4078.
Registro descomprimido: +0 nombre de la unidad (kana de medio ancho, NUL; campo de 0x1A bytes) … armas desde +0x44 en registros de 0x28:
  +0 índice (0..n-1) · +1 0 · +2 u16 ? · +4 u16 potencia · +6 u16 tipo/flags · +8 nombre SJIS/kana (NUL) …
  (en RAM el juego reordena las armas; el archivo trae el orden original)
Largos (2026-09-28, #13): nombre de unidad ≤ 21 bytes + NUL en +0x00..+0x15 (+0x16..+0x19 = aa ab ac ad en las 486:
  constante, no se toca; +0x14..+0x15 es basura del buffer de origen, los nombres de 21 bytes la pisan). Nombre de
  arma ≤ 19 bytes + NUL en +0x08..+0x1B (+0x1C ya es un campo de datos: 0x20 en 458 armas).
Uso: robot_raf.py [--json salida.jsonl] [--repack salida.RAF]   (--repack: recomprime todo sin cambios, para probar)
     robot_raf.py build salida.RAF [--report salida.csv]
       → nombres en inglés desde glossary/glossary.csv (en_final si entra, si no en_short; unidades por robot_id vía
         glossary/units_en.csv) + recompresión; falla si algo no entra o queda sin traducción
"""
import csv, json, os, struct, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(WORK, 'iso_jp', 'UNITPRAM', 'ROBOT.RAF')
GLOSSARY = os.path.join(WORK, 'glossary', 'glossary.csv')
UNITS_EN = os.path.join(WORK, 'glossary', 'units_en.csv')
N, F = 4096, 18
W0, WSIZE = 0x44, 0x28
UNAME_MAX, UNAME_FIELD = 21, 0x16        # +0x00..+0x15
WNAME, WNAME_MAX = 0x08, 19              # +0x08..+0x1B
EN_SPACE = b'\xa0'                       # espacio angosto del inglés (notes/fuente_en.md)
# casilleros de relleno (potencia 0; Gundam, Core Fighter…): no están en el glosario
EXTRA_WEAPONS = {'ﾀﾞﾐ-': 'Dummy'}


def lzss(src, size):
    ring = bytearray(N)
    r, out, p = N - F, bytearray(), 0
    while len(out) < size and p < len(src):
        flags = src[p]; p += 1
        for bit in range(8):
            if len(out) >= size or p >= len(src):
                break
            if flags >> bit & 1:
                c = src[p]; p += 1
                out.append(c); ring[r] = c; r = (r + 1) % N
            else:
                b1, b2 = src[p], src[p + 1]; p += 2
                pos, ln = b1 | (b2 & 0xF0) << 4, (b2 & 0x0F) + 3
                for k in range(ln):
                    c = ring[(pos + k) % N]
                    out.append(c); ring[r] = c; r = (r + 1) % N
    return bytes(out)


def lzss_compress(data):
    """Compresor compatible con lzss(): búsqueda voraz con cadenas de hash sobre lo ya escrito (distancia ≥ largo,
    para que la copia no lea bytes que el decodificador todavía no escribió). No reproduce el archivo original
    byte a byte (no hace falta): solo tiene que decodificar igual."""
    out = bytearray()
    heads = {}                      # 3 bytes → posiciones previas (más recientes al final)
    i, n = 0, len(data)
    while i < n:
        flag_pos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_pos = 0, 0
            key = data[i:i + 3]
            if len(key) == 3:
                for j in reversed(heads.get(key, [])[-64:]):
                    if i - j > N - F:
                        break
                    ln = 0
                    while ln < F and i + ln < n and data[j + ln] == data[i + ln] and j + ln < i:
                        ln += 1
                    if ln > best_len:
                        best_len, best_pos = ln, j
                        if ln == F:
                            break
            if best_len >= 3:
                pos = (N - F + best_pos) % N          # posición en el anillo del decodificador
                out += bytes([pos & 0xFF, (pos >> 4) & 0xF0 | (best_len - 3)])
                step = best_len
            else:
                flags |= 1 << bit
                out.append(data[i]); step = 1
            for k in range(i, i + step):
                heads.setdefault(data[k:k + 3], []).append(k)
            i += step
        out[flag_pos] = flags
    return bytes(out)


def pack_entry(raw):
    return struct.pack('<II', len(raw), 0) + lzss_compress(raw)


def entries(data):
    n = struct.unpack_from('<I', data, 0)[0]
    offs = struct.unpack_from('<%dI' % n, data, 4)
    base = 4 + 4 * n
    for i in range(n):
        end = base + offs[i + 1] if i + 1 < n else len(data)
        chunk = data[base + offs[i]:end]
        size = struct.unpack_from('<I', chunk, 0)[0]
        yield i, size, lzss(chunk[8:], size)


def build_raf(raws):
    """Arma un ROBOT.RAF con los registros descomprimidos dados (lista en orden de id)."""
    packed = [pack_entry(r) for r in raws]
    offs, cur = [], 0
    for p in packed:
        offs.append(cur); cur += len(p)
    return struct.pack('<I%dI' % len(raws), len(raws), *offs) + b''.join(packed)


def cstr(b):
    return b.split(b'\0')[0].decode('cp932', 'replace')


def parse(rec):
    unit = {'name': cstr(rec[0:0x1A]), 'weapons': []}   # campo de 26 bytes (nombres hasta 21 + NUL; resto relleno)
    for k in range(16):
        w = rec[W0 + k * WSIZE:W0 + (k + 1) * WSIZE]
        if len(w) < WSIZE or w[0] & 0x0F != k or not w[8]:   # +0: índice en los 4 bits bajos, banderas arriba
            break                                            # (0x16 = Fin Funnel, 0x37 = arma 7 de ν Gundam…)
        unit['weapons'].append({'idx': w[0], 'power': struct.unpack_from('<H', w, 4)[0],
                                'name': cstr(w[8:0x1c]), 'raw': w.hex()})
    return unit


def norm(s):
    """Misma forma comparable que glossary_build.norm (medio ancho → ancho completo, '-' tras kana → ー, = → ・)."""
    import re, unicodedata
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(?<=[ァ-ヴー])-', 'ー', s).replace('=', '・').replace('＝', '・')
    return re.sub(r'\s+', '', s)


def to_game(text):
    from sjis_text import encode
    return encode(text).replace(b' ', EN_SPACE)


def fit(en, short, maxlen):
    """en_final si entra; si no, en_short. None si ninguno entra."""
    for t in (en, short):
        if t and len(to_game(t)) <= maxlen:
            return t
    return None


def english_names():
    """(unidades {robot_id: en}, armas {nombre del juego: en}, problemas). Fuente: glossary.csv (ya aplica
    decisiones.csv y weapons_review.csv); units_en.csv solo da robot_id → jp."""
    rows = list(csv.DictReader(open(GLOSSARY, encoding='utf-8')))
    gu = {norm(r['jp']): r for r in rows if r['category'] == 'unit'}
    gw = {norm(r['jp']): r for r in rows if r['category'] == 'weapon'}
    units, weapons, problems = {}, {}, []
    for u in csv.DictReader(open(UNITS_EN, encoding='utf-8')):
        g = gu.get(norm(u['jp_norm']))
        en = fit(g['en_final'], g['en_short'], UNAME_MAX) if g else fit(u['en'], u['en_short'], UNAME_MAX)
        if en is None:
            problems.append(f'unidad {u["robot_id"]} {u["jp_game"]}: sin nombre inglés de ≤{UNAME_MAX} bytes')
        units[int(u['robot_id'])] = en
    data = open(SRC, 'rb').read()
    for _, _, rec in entries(data):
        for w in parse(rec)['weapons']:
            jp = w['name']
            if jp in weapons:
                continue
            g = gw.get(norm(jp))
            en = EXTRA_WEAPONS.get(jp) or (fit(g['en_final'], g['en_short'], WNAME_MAX) if g else None)
            if en is None:
                problems.append(f'arma {jp}: ' + ('sin traducción en el glosario' if not g else
                                                 f'ni en_final ni en_short entran en {WNAME_MAX} bytes'))
            weapons[jp] = en
    return units, weapons, problems


def put(rec, off, field, text):
    raw = to_game(text)
    assert len(raw) < field
    rec[off:off + field] = raw + b'\0' * (field - len(raw))   # NUL hasta el fin del campo: nada de 0xDE/0xDF sueltos


def apply_names(data, units, weapons):
    """Registros con los nombres en inglés (lista en orden de id) + filas del informe."""
    raws, report = [], []
    for i, _, rec in entries(data):
        rec = bytearray(rec)
        u = parse(rec)
        if units.get(i):
            put(rec, 0, UNAME_FIELD, units[i])
            report.append(('unidad', i, '', u['name'], units[i], len(to_game(units[i]))))
        for k, w in enumerate(u['weapons']):
            en = weapons.get(w['name'])
            if en:
                put(rec, W0 + k * WSIZE + WNAME, WNAME_MAX + 1, en)
                report.append(('arma', i, k, w['name'], en, len(to_game(en))))
        raws.append(bytes(rec))
    return raws, report


def build(out, report_path=None):
    data = open(SRC, 'rb').read()
    units, weapons, problems = english_names()
    if problems:
        raise SystemExit('ERROR ' + '\nERROR '.join(problems))
    raws, report = apply_names(data, units, weapons)
    raf = build_raf(raws)
    # control: al descomprimir, solo cambiaron los campos de nombre
    again = [rec for _, _, rec in entries(raf)]
    orig = [rec for _, _, rec in entries(data)]
    assert again == raws and len(again) == len(orig)
    for a, o in zip(again, orig):
        u = parse(o)
        allowed = set(range(UNAME_FIELD))
        for k in range(len(u['weapons'])):
            base = W0 + k * WSIZE + WNAME
            allowed |= set(range(base, base + WNAME_MAX + 1))
        assert len(a) == len(o) and all(a[j] == o[j] for j in range(len(o)) if j not in allowed)
    open(out, 'wb').write(raf)
    nu = sum(1 for r in report if r[0] == 'unidad'); nw = sum(1 for r in report if r[0] == 'arma')
    print(f'{nu} unidades y {nw} registros de arma ({len(weapons)} nombres distintos) en inglés; '
          f'{len(data)} → {len(raf)} bytes → {out}')
    if report_path:
        with open(report_path, 'w', encoding='utf-8', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['tipo', 'robot_id', 'arma', 'jp', 'en', 'bytes'])
            wr.writerows(report)
    return raf


def main():
    if len(sys.argv) > 2 and sys.argv[1] == 'build':
        rp = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else None
        build(sys.argv[2], rp)
        return
    data = open(SRC, 'rb').read()
    units = []
    bad = 0
    for i, size, rec in entries(data):
        if len(rec) != size:
            bad += 1
        u = parse(rec)
        u['id'] = i
        units.append(u)
    nw = sum(len(u['weapons']) for u in units)
    print(f'{len(units)} entradas, {bad} con tamaño inesperado, {nw} armas')
    if '--repack' in sys.argv:
        path = sys.argv[sys.argv.index('--repack') + 1]
        raws = [rec for _, _, rec in entries(data)]
        open(path, 'wb').write(build_raf(raws))
        again = [rec for _, _, rec in entries(open(path, 'rb').read())]
        print('repack →', path, 'idéntico al descomprimir:', again == raws)
    if '--json' in sys.argv:
        path = sys.argv[sys.argv.index('--json') + 1]
        with open(path, 'w', encoding='utf-8') as f:
            for u in units:
                f.write(json.dumps(u, ensure_ascii=False) + '\n')
        print('→', path)
    return units


if __name__ == '__main__':
    main()
