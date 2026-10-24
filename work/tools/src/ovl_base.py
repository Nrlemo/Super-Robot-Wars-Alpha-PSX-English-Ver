"""Estima la dirección de enlace de cada overlay (OVL/*_GRP.BIN): la base b que hace que más punteros del código
(palabras de 32 bits y pares lui/addiu|ori) caigan en b + inicio de un string SJIS del propio archivo."""
import collections, glob, os, re, struct, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STR = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\xfc]|[\x20-\x7e\xa1-\xdf]){2,}\x00')


def pointers(d):
    ws = struct.unpack_from('<%dI' % (len(d) // 4), d, 0)
    out = [w for w in ws if 0x80010000 <= w < 0x80200000]
    hi = {}
    for w in ws:
        op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xFFFF
        if op == 0x0F:                                   # lui rt, imm
            hi[rt] = imm << 16
        elif op in (0x09, 0x0D) and rs in hi:            # addiu / ori rt, rs, imm
            lo = imm - 0x10000 if (op == 0x09 and imm & 0x8000) else imm
            v = (hi[rs] + lo) & 0xFFFFFFFF
            if 0x80010000 <= v < 0x80200000:
                out.append(v)
    return out


def strings(d):
    return {m.start() for m in STR.finditer(d) if re.search(rb'[\x81-\x9f\xe0-\xfc]', m.group())}


def estimate(d):
    ps, ss = pointers(d), strings(d)
    votes = collections.Counter()
    for p in set(ps):
        for s in ss:
            b = p - s
            if 0x80010000 <= b < 0x80200000:
                votes[b] += 1
    return votes.most_common(3), len(ss)


if __name__ == '__main__':
    for f in sorted(glob.glob(os.path.join(WORK, 'iso_jp', 'OVL', '*_GRP.BIN'))):
        d = open(f, 'rb').read()
        top, n = estimate(d)
        print(f"{os.path.basename(f):14} strings {n:4}  " + '  '.join(f'{b:#x}:{v}' for b, v in top))
