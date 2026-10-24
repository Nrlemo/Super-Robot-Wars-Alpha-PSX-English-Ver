"""Inventario de textos de menú en el EXE y los overlays: dirección, lugar disponible y referencias.

Direcciones de enlace (verificadas con volcados de RAM y por votación de punteros, ver notes/menus.md):
  0x800A8920 PRM · 0x800D61D8 SNMP IMIS END SNDM PRO · 0x800FF190 COMM TITL COMA · 0x8011308C BTL ENTR SNDU MOVE MPWP
  EXE SLPS_026.36: cabecera 0x800, carga en 0x80010000.
Referencias: 'ptr' = palabra de 32 bits con la dirección exacta (tablas); 'code' = par lui + addiu/ori que la arma.
'room' = bytes desde el inicio del string hasta el siguiente byte no nulo tras su NUL (lugar para reemplazo in situ).
Uso: ovl_strings.py → dump/ovl_strings.jsonl + resumen
"""
import collections, glob, json, os, re, struct

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BASES = {'PRM': 0x800A8920, 'SNMP': 0x800D61D8, 'IMIS': 0x800D61D8, 'END': 0x800D61D8, 'SNDM': 0x800D61D8,
         'PRO': 0x800D61D8, 'COMM': 0x800FF190, 'TITL': 0x800FF190, 'COMA': 0x800FF190, 'BTL': 0x8011308C,
         'ENTR': 0x8011308C, 'SNDU': 0x8011308C, 'MOVE': 0x8011308C, 'MPWP': 0x8011308C}
STR = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\xfc]|[\x09\x0a\x20-\x7e\xa1-\xdf]){2,}\x00')
ONE = re.compile(rb'(?<=\x00)([\x81-\x9f\xe0-\xfc][\x40-\xfc])\x00')


def refs(d, base):
    """dirección → lista de (tipo, offset de la instrucción/palabra)."""
    out = collections.defaultdict(list)
    n = len(d) // 4
    ws = struct.unpack_from('<%dI' % n, d, 0)
    hi = {}
    soft = {}   # lui que sobreviven a j/jr (addiu en otra rama, p. ej. delay slot tras un beq), a ≤ 64 bytes
    for i, w in enumerate(ws):
        if 0x80010000 <= w < 0x80200000:
            out[w].append(('ptr', i * 4))
        op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xFFFF
        if op == 0x0F:
            hi[rt] = soft[rt] = (imm << 16, i * 4)
        elif op in (0x09, 0x0D) and rs in hi:
            lo = imm - 0x10000 if (op == 0x09 and imm & 0x8000) else imm
            v = (hi[rs][0] + lo) & 0xFFFFFFFF
            out[v].append(('code', i * 4))
        elif op in (0x09, 0x0D) and rs in soft and i * 4 - soft[rs][1] <= 64:
            lo = imm - 0x10000 if (op == 0x09 and imm & 0x8000) else imm
            v = (soft[rs][0] + lo) & 0xFFFFFFFF
            out[v].append(('code', i * 4))
        if op in (0x02, 0x03) or (op == 0 and (w & 0x3F) in (8, 9)):   # j/jal/jr/jalr: los lui dejan de valer
            hi = {}
    return out


def scan(name, d, base, hdr=0):
    r = refs(d, base)
    rows = []
    for m in STR.finditer(d):
        s = m.group()[:-1]
        # texto japonés: algún carácter SJIS de 2 bytes, o ≥2 kana de medio ancho (etiquetas de menú: ｾｰﾌﾞ, ﾛｰﾄﾞ)
        if len(s) < 2 or not (re.search(rb'[\x81-\x9f\xe0-\xfc][\x40-\xfc]', s)
                              or len(re.findall(rb'[\xa6-\xdf]', s)) >= 2):
            continue
        try:
            jp = s.decode('cp932')
        except UnicodeDecodeError:
            continue
        off = m.start()
        addr = base + off - hdr
        end = m.end()
        while end < len(d) and d[end] == 0:
            end += 1
        rr = r.get(addr, [])
        rows.append({'file': name, 'off': off, 'addr': f'{addr:#x}', 'jp': jp, 'bytes': len(s),
                     'room': end - off - 1, 'refs': [f'{t}@{o:#x}' for t, o in rr]})
    # strings de UN carácter SJIS (空 陸 海 宇, 機, 魂, 愛, 姓/名…): el patrón de arriba pide ≥ 2; se aceptan solo si
    # empiezan tras un NUL y tienen alguna referencia (si no, son ruido de código)
    for m in ONE.finditer(d):
        off = m.start(1)
        addr = base + off - hdr
        if not r.get(addr):
            continue
        try:
            jp = m.group(1).decode('cp932')
        except UnicodeDecodeError:
            continue
        end = off + 3
        while end < len(d) and d[end] == 0:
            end += 1
        rows.append({'file': name, 'off': off, 'addr': f'{addr:#x}', 'jp': jp, 'bytes': 2,
                     'room': end - off - 1, 'refs': [f'{t}@{o:#x}' for t, o in r[addr]]})
    rows.sort(key=lambda x: x['off'])
    return rows


def main():
    rows = []
    exe = open(os.path.join(WORK, 'iso_jp', 'SLPS_026.36'), 'rb').read()
    rows += scan('EXE', exe, 0x80010000 - 0x800, hdr=0)
    for f in sorted(glob.glob(os.path.join(WORK, 'iso_jp', 'OVL', '*_GRP.BIN'))):
        name = os.path.basename(f).split('_')[0]
        rows += scan(name, open(f, 'rb').read(), BASES[name])
    dst = os.path.join(WORK, 'dump', 'ovl_strings.jsonl')
    with open(dst, 'w', encoding='utf-8') as fo:
        for r in rows:
            fo.write(json.dumps(r, ensure_ascii=False) + '\n')
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        kinds = {x.split('@')[0] for x in r['refs']}
        k = 'sin ref' if not kinds else '+'.join(sorted(kinds))
        by[r['file']][k] += 1
    print(len(rows), 'strings →', dst)
    for f, c in by.items():
        print(f'  {f:5} ' + '  '.join(f'{k}:{v}' for k, v in c.most_common()))


if __name__ == '__main__':
    main()
