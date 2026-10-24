"""SNMAP/DEADMESS.BIN (frases al ser derribado) y SNMAP/EM.BIN (mensajes al suspender): extracción y reconstrucción.

Formato DEADMESS.BIN (262.208 bytes; verificado 2026-09-27 por análisis estático, todos los bytes contabilizados):
  0x00  bitmap de 64 bytes = 512 bits, LSB primero: bit j = el piloto j tiene frase (272 bits en 1; coincide
        exactamente con los pares de slots no vacíos: 512/512)
  0x40  1024 slots fijos de 256 bytes = 512 pilotos × 2 variantes; slot = 2*piloto + variante
        slot: u32 tipo (0..5, significado sin verificar: ¿expresión del retrato?) · 252 bytes SJIS terminados en NUL
        (relleno con 0; 4 slots traen basura vieja después del NUL: se conserva para reconstruir idéntico)
  piloto = ID de UNITPRAM/PILOT.BIN (0..468; verificado por los nombres). Las 2 variantes tienen el mismo texto salvo en 6 pilotos.
Formato EM.BIN (85.264 bytes):
  30 registros fijos de 264 bytes (0x0000..0x1EEF):
        u16 a (¿?) · u16 b (¿BGM/grupo? corridas consecutivas de igual b = misma escena) ·
        u16 piloto (ID de PILOT.BIN; el nombre también va dentro del texto: 「ライ「…」」) · u16 flag (0/1, ¿?) ·
        256 bytes SJIS terminados en NUL (relleno con 0). Mezcla ASCII de 1 byte ('?', '!', ' ') con SJIS.
  0x1EF0 TIM 8bpp 320×240 con CLUT (fondo de la pantalla de suspensión; sin texto) hasta el final del archivo.
Ninguno de los dos tiene punteros: los slots son de tamaño fijo y el ejecutable calcula la posición (sin verificar en
el código). Por eso el texto inglés puede ser más largo que el japonés, pero solo hasta llenar el slot
(DEADMESS: 251 bytes + NUL; EM: 255 bytes + NUL); el tamaño del archivo no cambia.
0x0A = salto de línea; en inglés el espacio se codifica 0xA0 (ver notes/fuente_en.md).
Uso:
  deadmess_em.py dump [dir]                           → dump/deadmess.jsonl y dump/em.jsonl (o en dir)
  deadmess_em.py build deadmess|em entrada.jsonl salida.BIN
                                                      → reconstruye usando "en" cuando no está vacío
  deadmess_em.py selftest                             → reconstrucción sin cambios == original + prueba de textos largos
"""
import json, os, struct, sys

sys.path.insert(0, os.path.dirname(__file__))
from script_bin import encode_en  # noqa: E402

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SNMAP = os.path.join(WORK, 'iso_jp', 'SNMAP')
PILOT = os.path.join(WORK, 'iso_jp', 'UNITPRAM', 'PILOT.BIN')
DUMP = os.path.join(WORK, 'dump')

FILES = {
    #            archivo          base  paso  cabecera slots  tamaño
    'deadmess': ('DEADMESS.BIN', 0x40, 0x100, 4, 1024, 262208),
    'em':       ('EM.BIN',       0x00, 0x108, 8, 30,   85264),
}
EM_TIM = 0x1EF0


def src(kind):
    return open(os.path.join(SNMAP, FILES[kind][0]), 'rb').read()


def pilot_names():
    p = open(PILOT, 'rb').read()
    n = struct.unpack_from('<I', p)[0]
    return [p[4 + j * 0x70 + 4:4 + j * 0x70 + 20].split(b'\0')[0].decode('cp932', 'replace') for j in range(n)]


def slots(kind, data):
    """→ lista de (índice, campos_cabecera(bytes), texto(bytes), resto_después_del_NUL(bytes))."""
    _, base, step, hdr, n, size = FILES[kind]
    assert len(data) == size, f'{kind}: tamaño {len(data)} != {size}'
    out = []
    for i in range(n):
        s = data[base + i * step:base + (i + 1) * step]
        body = s[hdr:]
        z = body.index(b'\0')
        out.append((i, s[:hdr], body[:z], body[z:]))
    return out


def check(kind, data):
    """Validación estructural: que cada byte del archivo esté explicado."""
    ss = slots(kind, data)
    if kind == 'deadmess':
        bm = data[:0x40]
        for j in range(512):
            bit = (bm[j >> 3] >> (j & 7)) & 1
            has = bool(ss[2 * j][2]) and bool(ss[2 * j + 1][2])
            none = not ss[2 * j][2] and not ss[2 * j + 1][2]
            assert (bit and has) or (not bit and none), f'piloto {j}: bitmap {bit} no coincide con los slots'
            if not bit:
                assert not any(ss[2 * j][1] + ss[2 * j + 1][1]), f'piloto {j}: slot vacío con cabecera'
    else:
        assert data[EM_TIM:EM_TIM + 4] == b'\x10\0\0\0', 'EM: no hay TIM en 0x1EF0'
        o = EM_TIM + 8
        for _ in range(2):  # bloque CLUT + bloque imagen
            o += struct.unpack_from('<I', data, o)[0]
        assert o == len(data), f'EM: el TIM termina en {o:#x}, el archivo en {len(data):#x}'
    return ss


def dump(out_dir=DUMP):
    names = pilot_names()
    os.makedirs(out_dir, exist_ok=True)
    counts = {}
    for kind in FILES:
        data = src(kind)
        ss = check(kind, data)
        rows = []
        for i, h, t, _ in ss:
            if not t:
                continue
            if kind == 'deadmess':
                pid, var = divmod(i, 2)
                other = ss[i ^ 1][2]
                r = {'slot': i, 'pilot': pid, 'variant': var, 'type': struct.unpack('<I', h)[0],
                     'name': names[pid] if pid < len(names) else '', 'same_as_other_variant': t == other}
            else:
                a, b, pid, flag = struct.unpack('<4H', h)
                r = {'rec': i, 'a': a, 'b': b, 'pilot': pid, 'flag': flag,
                     'name': names[pid] if pid < len(names) else ''}
            r.update(jp=t.decode('cp932'), en='')
            rows.append(r)
        out = os.path.join(out_dir, kind + '.jsonl')
        with open(out, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        counts[kind] = len(rows)
        print(f'{out}: {len(rows)} textos')
    return counts


def load_en(kind, path):
    key = 'slot' if kind == 'deadmess' else 'rec'
    en = {}
    for line in open(path, encoding='utf-8'):
        if line.strip():
            r = json.loads(line)
            t = r.get('en') or r.get('en_ref')      # en_ref: inglés de referencia de un fork (kit.py pivot)
            if t:
                en[r[key]] = t
    if kind == 'deadmess':  # variante sin traducir con el mismo japonés que su par → usa la traducción del par
        rows = [json.loads(x) for x in open(path, encoding='utf-8') if x.strip()]
        for r in rows:
            if r['slot'] not in en and r.get('same_as_other_variant') and (r['slot'] ^ 1) in en:
                en[r['slot']] = en[r['slot'] ^ 1]
    return en


def build(kind, data, en):
    """Reemplaza el texto de los slots indicados en `en` ({slot: str inglés}); el resto queda idéntico."""
    _, base, step, hdr, n, _ = FILES[kind]
    ss = check(kind, data)
    out = bytearray(data)
    room = step - hdr
    for i, s in en.items():
        if not ss[i][2]:
            raise ValueError(f'{kind} slot {i}: estaba vacío en el original (no soportado)')
        b = encode_en(s)
        if len(b) > room:
            raise ValueError(f'{kind} slot {i}: {len(b)} bytes (con NUL) > {room} disponibles: {s!r}')
        o = base + i * step + hdr
        out[o:o + room] = b + b'\0' * (room - len(b))
    return bytes(out)


def selftest():
    ok = True
    for kind in FILES:
        data = src(kind)
        ss = check(kind, data)
        _, base, step, hdr, n, size = FILES[kind]
        # 1) reconstrucción desde las piezas parseadas
        if kind == 'deadmess':
            again = data[:0x40] + b''.join(h + t + r for _, h, t, r in ss)
        else:
            again = b''.join(h + t + r for _, h, t, r in ss) + data[EM_TIM:]
        same = again == data and build(kind, data, {}) == data
        # 2) todos los textos al máximo de largo en inglés → se releen iguales y nada más cambia
        room = step - hdr
        long_en = {i: ('Line %d ' % i + 'x' * room)[:room - 1] for i, _, t, _ in ss if t}
        big = build(kind, data, long_en)
        ss2 = check(kind, big)
        reread = all(ss2[i][2] == encode_en(s)[:-1] for i, s in long_en.items())
        heads = all(a[1] == b[1] for a, b in zip(ss, ss2))
        rest = big[:0x40] == data[:0x40] if kind == 'deadmess' else big[EM_TIM:] == data[EM_TIM:]
        try:
            build(kind, data, {next(iter(long_en)): 'x' * room}); too_long = False
        except ValueError:
            too_long = True
        print(f'{kind}: {len(data)} bytes, {sum(1 for x in ss if x[2])} textos · reconstrucción idéntica: {same} · '
              f'textos de {room - 1} bytes: releídos {reread}, cabeceras {heads}, resto {rest} · '
              f'texto demasiado largo rechazado: {too_long}')
        ok &= same and reread and heads and rest and too_long and len(big) == size
    print('OK' if ok else 'FALLÓ')
    return ok


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'selftest'
    if cmd == 'dump':
        dump(*sys.argv[2:3])
    elif cmd == 'build':
        kind, inp, out = sys.argv[2].lower(), sys.argv[3], sys.argv[4]
        en = load_en(kind, inp)
        open(out, 'wb').write(build(kind, src(kind), en))
        print(f'{out}: {len(en)} textos reemplazados')
    elif cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
