"""Aplica un parche PPF 2.0 sobre una COPIA de la imagen (nunca in-place sobre el original).

Uso: ppf_apply.py <imagen_origen.bin> <parche.ppf> <imagen_destino.bin>
"""
import shutil
import struct
import sys
from pathlib import Path

PPF2_BLOCKCHECK_OFFSET = 0x9320  # bloque de validación de 1024 bytes (PPF 2.0)


def parse_ppf2(data: bytes):
    if data[:5] != b'PPF20':
        raise ValueError(f'no es PPF 2.0: {data[:5]!r}')
    desc = data[6:56].decode('latin1').strip()
    target_size = struct.unpack_from('<I', data, 56)[0]
    block = data[60:60 + 1024]
    records, o = [], 60 + 1024
    diz = data.find(b'@BEGIN_FILE_ID.DIZ')
    end = diz if diz != -1 else len(data)
    while o < end:
        off, ln = struct.unpack_from('<IB', data, o)
        records.append((off, data[o + 5:o + 5 + ln]))
        o += 5 + ln
    return desc, target_size, block, records


def main(src: str, ppf: str, dst: str) -> None:
    src_p, dst_p = Path(src).resolve(), Path(dst).resolve()
    if src_p == dst_p:
        sys.exit('destino == origen: me niego a parchear in-place')
    desc, target_size, block, records = parse_ppf2(Path(ppf).read_bytes())
    print(f'PPF: {desc} | {len(records)} registros | {sum(len(r) for _, r in records)} bytes')
    if src_p.stat().st_size != target_size:
        sys.exit(f'tamaño no coincide: {src_p.stat().st_size} != {target_size}')
    with open(src_p, 'rb') as f:
        f.seek(PPF2_BLOCKCHECK_OFFSET)
        if f.read(1024) != block:
            sys.exit('bloque de validación PPF no coincide: imagen incorrecta')
    shutil.copyfile(src_p, dst_p)
    with open(dst_p, 'r+b') as f:
        for off, payload in records:
            f.seek(off)
            f.write(payload)
    print(f'OK → {dst_p}')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
