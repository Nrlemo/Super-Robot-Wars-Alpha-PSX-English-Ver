"""Contenedores con tabla de offsets absolutos + entradas LZSS (BATTLE/COMMON.BIN, BUSTUP/MAP.BIN, BACK.BIN,
CHARA.BIN, BATTLE/UNIT.BIN).

Formato: u32 offset[n] (offset[0] = 4·n = fin de la tabla), alineados a 4. Cada entrada es
  - comprimida: u32 tamaño descomprimido, u32 0, datos LZSS (el mismo de ROBOT.RAF), o
  - cruda (datos de animación, etc.): cualquier otra cosa; se copia tal cual.

Reconstrucción: las entradas sin cambios conservan sus bytes originales; una entrada modificada se recomprime y,
si entra en su hueco original, se escribe **en el lugar** (mismos offsets y tamaño de archivo, relleno con 0).
Si no entra, se rearman los offsets a partir de ahí (el archivo crece) y se avisa.

Uso: lzpack.py list <archivo> | selftest <archivo>...
"""
import struct
import sys

from robot_raf import N, F, lzss


def _match(data, i, heads, depth):
    n, best_len, best_pos = len(data), 0, 0
    for j in reversed(heads.get(data[i:i + 3], [])[-depth:]):
        if i - j > N - F:
            break
        ln = 0
        while ln < F and i + ln < n and data[j + ln] == data[i + ln]:  # solapar (j + ln ≥ i) es válido:
            ln += 1                                                     # lzss() escribe el anillo al copiar
        if ln > best_len:
            best_len, best_pos = ln, j
            if ln == F:
                break
    return best_len, best_pos


def lzss_compress(data, depth=256):
    """Compresor para lzss() con copias solapadas (las tiras de transparente) y lazy matching de 1 paso.
    Comprime más que robot_raf.lzss_compress, que prohíbe solapar."""
    out, heads = bytearray(), {}
    i, n = 0, len(data)

    def add(a, b):
        for k in range(a, b):
            heads.setdefault(data[k:k + 3], []).append(k)
    while i < n:
        flag_pos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n:
                break
            ln, pos = _match(data, i, heads, depth) if i + 3 <= n else (0, 0)
            if ln >= 3 and ln < F and i + 4 <= n:
                add(i, i + 1)
                ln2, _ = _match(data, i + 1, heads, depth)
                heads[data[i:i + 3]].pop()
                if ln2 > ln + 1:
                    ln = 0                      # mejor emitir un literal y tomar la copia siguiente
            if ln >= 3:
                p = (N - F + pos) % N
                out += bytes([p & 0xFF, (p >> 4) & 0xF0 | (ln - 3)])
            else:
                flags |= 1 << bit
                out.append(data[i]); ln = 1
            add(i, i + ln)
            i += ln
        out[flag_pos] = flags
    return bytes(out)


def table(data):
    """Offsets de las entradas. Estándar: u32 offset[n] con offset[0] = 4·n. Variante (SNMAP/KIEFETIM.BIN, #271): la tabla
    ocupa más que sus offsets (offset[0] = 0x800), termina en un 0 y el último offset es el fin del archivo (centinela)."""
    first = struct.unpack_from('<I', data, 0)[0]
    n = first // 4
    offs = list(struct.unpack_from(f'<{n}I', data, 0))
    if 0 in offs:   # tabla con relleno de ceros
        offs = offs[:offs.index(0)]
        if offs and offs[-1] == len(data):
            offs.pop()
        return offs, True
    return offs, False


def read(data):
    offs, padded = table(data)
    n = len(offs)
    ends = offs[1:] + [len(data)]
    out = []
    for i in range(n):
        chunk = data[offs[i]:ends[i]]
        e = {'i': i, 'off': offs[i], 'chunk': chunk, 'raw': None}
        if len(chunk) > 8:
            size, zero = struct.unpack_from('<II', chunk, 0)
            if zero == 0 and 0 < size < 1 << 20:
                try:
                    e['raw'] = lzss(chunk[8:], size)
                except IndexError:
                    pass
        out.append(e)
    return out


def build(data, repl):
    """repl = {índice: datos descomprimidos nuevos}. Devuelve (bytes, avisos)."""
    ents = read(data)
    chunks = [e['chunk'] for e in ents]
    warn, inplace = [], True
    for i, raw in sorted(repl.items()):
        if ents[i]['raw'] is None:
            raise ValueError(f'entrada {i}: no es LZSS')
        if raw == ents[i]['raw']:
            continue
        new = struct.pack('<II', len(raw), 0) + lzss_compress(raw)
        new += b'\0' * (-len(new) % 4)
        if len(new) <= len(chunks[i]):
            chunks[i] = new + b'\0' * (len(chunks[i]) - len(new))
        else:
            warn.append(f'entrada {i}: {len(new)} B > hueco {len(chunks[i])} B → offsets reubicados')
            chunks[i] = new
            inplace = False
    if inplace:
        out = bytearray(data)
        for e, c in zip(ents, chunks):
            out[e['off']:e['off'] + len(c)] = c
        return bytes(out), warn
    if table(data)[1]:   # tabla con relleno: los offsets se reescriben dentro de la tabla y el centinela pasa a ser el fin
        first = ents[0]['off']
        offs, cur = [], first
        for c in chunks:
            offs.append(cur)
            cur += len(c)
        head = bytearray(data[:first])
        struct.pack_into(f'<{len(offs) + 1}I', head, 0, *offs, cur)
        return bytes(head) + b''.join(chunks), warn
    n = len(ents)
    offs, cur = [], ents[0]['off']
    for c in chunks:
        offs.append(cur)
        cur += len(c) + (-len(c) % 4)
    body = b''.join(c + b'\0' * (-len(c) % 4) for c in chunks)
    head = struct.pack(f'<{n}I', *offs)
    return head + data[len(head):ents[0]['off']] + body, warn


def selftest(paths):
    for p in paths:
        data = open(p, 'rb').read()
        ents = read(data)
        same, _ = build(data, {})
        assert same == data, p
        z = [e for e in ents if e['raw'] is not None]
        # recomprimir todas: tiene que decodificar igual; mide cuántas entran en su hueco
        fit = 0
        for e in z:
            c = lzss_compress(e['raw'])
            assert lzss(c, len(e['raw'])) == e['raw'], (p, e['i'])
            fit += 8 + len(c) <= len(e['chunk'])
        print(f'{p}: {len(ents)} entradas ({len(z)} LZSS), sin cambios = idéntico; recomprimidas OK, '
              f'{fit}/{len(z)} entran en su hueco')


if __name__ == '__main__':
    if sys.argv[1] == 'list':
        for e in read(open(sys.argv[2], 'rb').read()):
            print(e['i'], hex(e['off']), len(e['chunk']), 'LZSS→%d' % len(e['raw']) if e['raw'] is not None else 'crudo')
    elif sys.argv[1] == 'selftest':
        selftest(sys.argv[2:])
