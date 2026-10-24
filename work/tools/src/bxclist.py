"""BATTLE/BXCLIST.BIN (frases de combate de los pilotos): extracción y reconstrucción.

Formato (verificado 2026-09-27: los 470 bloques se recorren exactos, cada byte explicado; el significado de los
campos sale además del código que los lee, overlay OVL/BTL_GRP.BIN cargado en 0x8011308c: 0x80120dc0 = parser de
cabecera, 0x80121620 = frase de ataque, 0x80121934 = frase de defensa, 0x801211f8 / 0x80121574 = elegir frase).
  u32 offset[2048] absolutos (índice = id de piloto de UNITPRAM/PILOT.BIN; libres = 0xCDCDCDCD) · bloques seguidos
  tamaño de un bloque = offset[id+1] - offset[id] (el juego lo lee a un buffer de ese tamaño con malloc)
  bloque (todo little-endian, alineado a 4):
    +0x00 u8 nW (grupos de ataque) · u8 nX (armas) · u8 b2 (lo: nU, hi: nE) · u8 b3 (lo: nR, hi: nP)
    +0x04 u8 nS (grupos de defensa) · u8 b5 (lo: nRegBarrera, hi: nRegPilotoPropio) · u8 b6 (lo: nRegUnidad,
          hi: nRegUnidadEnemiga) · u8 b7 (lo: nRegCopiloto, hi: nRegPilotoEnemigo)
    +0x08 u32 A (registros de defensa) · B (u32 por frase) · C (u16 hablante por frase) · D (u16 offset por frase)
          · E (textos); todos relativos al inicio del bloque
    +0x1C W: nW × u16 "entrada" (+ u16 0 si nW es impar)
          X: nX × 4 bytes [modo, a, b, c] (a/b/c = índice en W, 0xFF = nada)
          R: nR × (u16 id copiloto, u16 0xFFFF, nX × 4 bytes como X)   → tabla de armas alternativa
          P: nP × (u16 id piloto enemigo, u16 entrada)                → frase de ataque contra ese piloto
          U: nU × (u16 id unidad propia,  u16 entrada)                → frase de ataque al pilotar esa unidad
          E: nE × (u16 id unidad enemiga, u16 entrada)                → frase de ataque contra esa unidad
    A:    registros de 12 bytes: u16 clave + 10 bytes (uno por situación): byte = (índice en S << 2) | cantidad
          orden: por defecto (clave 0), unidad propia, unidad enemiga, copiloto, piloto enemigo, piloto propio,
          barrera; luego S: nS × u16 entrada (+ u16 0 si impar)
    B:    n × u32 id global de frase (mismo id ⇒ mismo texto) · C: n × u16 (bits 0-9 id del piloto que habla,
          bits 10-12 expresión; + u16 0 si n impar) · D: n × u16 offset desde E (+ 0xFFFF si n impar)
    E:    n textos SJIS terminados en NUL, contiguos, en orden; relleno con '*' (0x2A) hasta múltiplo de 4
  "entrada" u16: bits 0-8 primera frase, bits 9-12 cantidad de alternativas, bits 13-15 frases por alternativa
  (el juego elige una alternativa al azar y muestra sus frases seguidas: diálogos piloto/copiloto)
  Bloques vacíos: 28 bytes en cero (pilotos sin frases); el del id 469 mide 0 bytes (fin del archivo).
Uso:
  bxclist.py dump [salida.jsonl]            → una línea JSON por frase (id piloto, índice, grupo, contexto, jp)
  bxclist.py build entrada.jsonl salida.BIN  → reconstruye usando "en" (o "en_ref") cuando no está vacío (puede ser más largo)
  bxclist.py selftest                        → reconstrucción sin cambios == original, y prueba con textos largos
"""
import json, os, struct, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(WORK, 'iso_jp', 'BATTLE', 'BXCLIST.BIN')
PILOT = os.path.join(WORK, 'iso_jp', 'UNITPRAM', 'PILOT.BIN')
NTABLE, UNUSED, HDR = 2048, 0xCDCDCDCD, 0x1C
# situaciones de defensa (byte k de cada registro); nombres deducidos del contenido de las frases
SLOTS = ['derribado', 'daño_grave', 'daño_medio', 'daño_leve', 'esquiva', 'anulado', 'sin_contraataque',
         'fuera_de_alcance', 'escudo', 'imagen_residual']
# grupos de registros de defensa en orden de archivo: (nombre, byte de cabecera, nibble)
REC_GROUPS = [('unidad', 6, 0), ('unidad_enemiga', 6, 1), ('copiloto', 7, 0), ('piloto_enemigo', 7, 1),
              ('piloto_propio', 5, 1), ('barrera', 5, 0)]
# papel de a/b/c en X según el modo (0x801212b8)
ROLES = {0: ('ataque', 'contraataque', 'nombre_arma'), 1: ('secuencia1', 'secuencia2', 'secuencia3'),
         3: ('opcion1', 'opcion2a', 'opcion2b')}


def entry(v):
    """u16 de entrada → (primera frase, alternativas, frases por alternativa)."""
    return v & 0x1FF, (v >> 9) & 0xF, v >> 13


def pad4(n):
    return (-n) % 4


def parse_block(b):
    """Parsea un bloque verificando cada byte; devuelve dict o None si es un bloque vacío."""
    if len(b) == 0 or b == bytes(HDR):
        return None
    nW, nX, b2, b3, nS, b5, b6, b7 = b[:8]
    A, B, C, D, E = struct.unpack_from('<5I', b, 8)
    nU, nE, nR, nP = b2 & 15, b2 >> 4, b3 & 15, b3 >> 4
    h = {'W': list(struct.unpack_from('<%dH' % nW, b, HDR))}
    o = HDR + 2 * nW
    if nW & 1:
        assert b[o:o + 2] == b'\0\0'; o += 2
    h['X'] = [b[o + 4 * k:o + 4 * k + 4] for k in range(nX)]; o += 4 * nX
    h['R'] = []
    for _ in range(nR):
        key, fill = struct.unpack_from('<HH', b, o)
        assert fill == 0xFFFF
        h['R'].append((key, [b[o + 4 + 4 * k:o + 8 + 4 * k] for k in range(nX)])); o += 4 + 4 * nX
    for name, cnt in (('P', nP), ('U', nU), ('E', nE)):
        h[name] = [struct.unpack_from('<HH', b, o + 4 * k) for k in range(cnt)]; o += 4 * cnt
    assert o == A, ('A', o, A)
    recs = [('defecto', b[o:o + 12])]; o += 12
    for name, byte, nib in REC_GROUPS:
        for _ in range((b[byte] >> (4 * nib)) & 15):
            recs.append((name, b[o:o + 12])); o += 12
    h['recs'] = [(g, struct.unpack_from('<H', r)[0], list(r[2:])) for g, r in recs]
    assert h['recs'][0][1] == 0
    h['S'] = list(struct.unpack_from('<%dH' % nS, b, o)); o += 2 * nS
    if nS & 1:
        assert b[o:o + 2] == b'\0\0'; o += 2
    assert o == B, ('B', o, B)
    n = (C - B) // 4
    h['msgid'] = list(struct.unpack_from('<%dI' % n, b, B))
    h['spk'] = list(struct.unpack_from('<%dH' % n, b, C))
    assert C + 2 * n + 2 * (n & 1) == D and (n % 2 == 0 or b[C + 2 * n:D] == b'\0\0')
    offs = struct.unpack_from('<%dH' % n, b, D)
    assert D + 2 * n + 2 * (n & 1) == E and (n % 2 == 0 or b[D + 2 * n:E] == b'\xff\xff')
    h['text'], pos = [], 0
    for off in offs:
        assert off == pos, 'textos no contiguos'
        end = b.index(b'\0', E + off)
        h['text'].append(b[E + off:end]); pos = end + 1 - E
    tail = b[E + pos:]
    assert len(tail) == pad4(E + pos) and tail == b'*' * len(tail), 'relleno final'
    h['head'] = b[:D]                                    # todo lo anterior a la tabla de offsets de textos
    h['n'] = n
    # cobertura: W, P, U, E y S reparten las n frases en rangos contiguos, en orden
    ranges = [('W%d' % k, v) for k, v in enumerate(h['W'])] + \
             [('%s%d' % (g, k), v) for g in 'PUE' for k, (_, v) in enumerate(h[g])] + \
             [('S%d' % k, v) for k, v in enumerate(h['S'])]
    nxt = 0
    for _, v in ranges:
        st, cnt, ln = entry(v)
        assert st == nxt and cnt and ln, ('rango', st, nxt, hex(v))
        nxt += cnt * ln
    assert nxt == n, ('cobertura', nxt, n)
    h['ranges'] = ranges
    for x in h['X'] + [x for _, xs in h['R'] for x in xs]:
        assert x[0] in (0, 1, 3, 0xFF) and all(w == 0xFF or w < nW for w in x[1:]), x.hex()
    for _, _, sl in h['recs']:
        assert all(v == 0 or (v >> 2) + (v & 3) <= nS for v in sl)
    return h


def build_block(h, texts):
    """Rearma un bloque con una lista nueva de textos (bytes sin NUL)."""
    assert len(texts) == h['n']
    area, offs = bytearray(), []
    for t in texts:
        assert b'\0' not in t
        offs.append(len(area)); area += t + b'\0'
    assert offs[-1] < 0x10000, 'el área de textos del bloque supera 64 KB (offsets u16)'
    d = struct.pack('<%dH' % len(offs), *offs) + (b'\xff\xff' if len(offs) & 1 else b'')
    out = h['head'] + d + area
    return bytes(out + b'*' * pad4(len(out)))


def parse(data):
    offs = struct.unpack_from('<%dI' % NTABLE, data, 0)
    used = [i for i, o in enumerate(offs) if o != UNUSED]
    assert used == list(range(len(used))), 'ids usados no contiguos'
    assert offs[0] == 4 * NTABLE
    bounds = [offs[i] for i in used] + [len(data)]
    raws = [data[bounds[k]:bounds[k + 1]] for k in range(len(used))]
    assert all(bounds[k] <= bounds[k + 1] for k in range(len(used)))
    return raws, [parse_block(r) for r in raws]


def build(raws, blocks, new_texts=None):
    """new_texts: {(id, índice): bytes}. Devuelve el archivo completo."""
    new_texts = new_texts or {}
    out, offs = bytearray(), []
    for pid, (raw, h) in enumerate(zip(raws, blocks)):
        offs.append(4 * NTABLE + len(out))
        if h is None:
            out += raw; continue
        texts = [new_texts.get((pid, i), t) for i, t in enumerate(h['text'])]
        out += build_block(h, texts) if texts != h['text'] else raw
    table = offs + [UNUSED] * (NTABLE - len(offs))
    return struct.pack('<%dI' % NTABLE, *table) + bytes(out)


def encode_en(s):
    """Inglés → bytes del juego: espacio = 0xA0 (0x20 no se dibuja bien), salto de línea = 0x0A."""
    return s.encode('cp932').replace(b' ', b'\xa0')


def pilot_names():
    d = open(PILOT, 'rb').read()
    n = int.from_bytes(d[:2], 'little')
    return [d[4 + i * 0x70 + 4:4 + i * 0x70 + 0x28].split(b'\0')[0].decode('cp932', 'replace') for i in range(n)]


def contexts(h):
    """Para cada frase: grupo, alternativa/línea y quién la usa (armas, registros de defensa, clave)."""
    uses = {}
    for key_src, xs in [(None, h['X'])] + [(k, xs) for k, xs in h['R']]:
        for wi, x in enumerate(xs):
            for role, w in zip(ROLES.get(x[0], ('?', '?', '?')), x[1:]):
                if w != 0xFF:
                    u = {'arma': wi, 'papel': role}
                    if key_src is not None:
                        u['copiloto'] = key_src
                    uses.setdefault('W%d' % w, []).append(u)
    for g, key, sl in h['recs']:
        for slot, v in enumerate(sl):
            for e in range(v >> 2, (v >> 2) + (v & 3)):
                u = {'registro': g, 'situacion': SLOTS[slot]}
                if g != 'defecto':
                    u['clave'] = key
                uses.setdefault('S%d' % e, []).append(u)
    out = []
    for name, v in h['ranges']:
        st, cnt, ln = entry(v)
        kind = {'W': 'ataque_arma', 'P': 'ataque_vs_piloto', 'U': 'ataque_unidad_propia',
                'E': 'ataque_vs_unidad', 'S': 'defensa'}[name[0]]
        extra = {}
        if name[0] in 'PUE':
            extra['clave'] = h[name[0]][int(name[1:])][0]
        for a in range(cnt):
            for l in range(ln):
                out.append(dict(grupo=name, tipo=kind, alt=a, linea=l, lineas=ln, usos=uses.get(name, []), **extra))
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'selftest'
    data = open(SRC, 'rb').read()
    raws, blocks = parse(data)
    if cmd == 'selftest':
        again = build(raws, blocks, {})
        print('bloques:', len(blocks), 'con frases:', sum(h is not None for h in blocks),
              'frases:', sum(h['n'] for h in blocks if h))
        print('reconstrucción idéntica:', again == data, f'({len(again)} bytes)')
        # reconstruir forzando el rearmado de cada bloque (sin atajo "raw") también debe ser idéntico
        forced = struct.pack('<%dI' % NTABLE, *struct.unpack_from('<%dI' % NTABLE, data)) + b''.join(
            raw if h is None else build_block(h, h['text']) for raw, h in zip(raws, blocks))
        print('rearmado forzado idéntico:', forced == data)
        # prueba de estrés: todas las frases más largas → el archivo resultante se vuelve a parsear igual
        long_texts = {(pid, i): encode_en('LONGER TEST %d-%d ' % (pid, i) + 'x' * (i % 40))
                      for pid, h in enumerate(blocks) if h for i in range(h['n'])}
        big = build(raws, blocks, long_texts)
        raws2, blocks2 = parse(big)
        ok = all((h2 is None) == (h is None) and (h is None or
                 [long_texts[(pid, i)] for i in range(h['n'])] == h2['text'] and h2['head'] == h['head'])
                 for pid, (h, h2) in enumerate(zip(blocks, blocks2)))
        print('prueba con textos largos:', ok, f'({len(big)} bytes, bloque mayor {max(map(len, raws2))} vs '
              f'{max(map(len, raws))} original)')
    elif cmd == 'dump':
        dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, 'dump', 'bxclist.jsonl')
        names = pilot_names()
        nm = lambda i: names[i] if i < len(names) else '?'
        n = 0
        with open(dst, 'w', encoding='utf-8') as f:
            for pid, h in enumerate(blocks):
                if h is None:
                    continue
                for i, (ctx, t) in enumerate(zip(contexts(h), h['text'])):
                    spk = h['spk'][i] & 0x3FF
                    r = {'pilot': pid, 'pilot_name': nm(pid), 'idx': i, **ctx,
                         'speaker': spk, 'speaker_name': nm(spk), 'expr': (h['spk'][i] >> 10) & 7,
                         'msgid': h['msgid'][i], 'jp': t.decode('cp932'), 'en': ''}
                    f.write(json.dumps(r, ensure_ascii=False) + '\n'); n += 1
        print(n, 'frases →', dst)
    elif cmd == 'build':
        src, dst = sys.argv[2], sys.argv[3]
        new = {}
        for line in open(src, encoding='utf-8'):
            r = json.loads(line)
            en = r.get('en') or r.get('en_ref')     # en_ref: inglés de referencia de un fork (kit.py pivot)
            if en:
                h = blocks[r['pilot']]
                assert h is not None and r['idx'] < h['n'], (r['pilot'], r['idx'])
                new[(r['pilot'], r['idx'])] = encode_en(en)
        out = build(raws, blocks, new)
        parse(out)                                        # el resultado tiene que volver a parsear
        grow = [(len(a), len(b)) for a, b in zip(raws, parse(out)[0])]
        open(dst, 'wb').write(out)
        print(len(new), 'frases reemplazadas →', dst, f'({len(out)} bytes; original {len(data)})')
        big = max(b for _, b in grow)
        if big > max(len(r) for r in raws):
            print(f'AVISO: el bloque mayor mide {big} bytes (original máx. {max(len(r) for r in raws)}); '
                  'el juego lo lee a memoria dinámica (malloc): probar en emulador.')


if __name__ == '__main__':
    main()
